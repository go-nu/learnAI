import asyncio
import io
import random
import httpx
from PIL import Image as PILImage
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

mcp = FastMCP("ComfyUI Image Generator 🎨")

COMFYUI_URL = "http://220.80.16.79:8188"

# z-image-turbo 전용 고정 설정
UNET_MODEL  = "z_image_turbo_bf16.safetensors"
CLIP_MODEL  = "qwen_3_4b.safetensors"
VAE_MODEL   = "ae.safetensors"


def _build_workflow(
    prompt: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
) -> dict:
    return {
        # 1. UNET 모델 로드
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": UNET_MODEL,
                "weight_dtype": "default",
            },
        },
        # 2. AuraFlow 샘플링 설정 적용
        "2": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {
                "shift": 3.0,
                "model": ["1", 0],
            },
        },
        # 3. CLIP 로드 (Lumina2 타입)
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": CLIP_MODEL,
                "type": "lumina2",
                "device": "default",
            },
        },
        # 4. VAE 로드
        "4": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_MODEL},
        },
        # 5. 프롬프트 인코딩 (Positive)
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["3", 0],
            },
        },
        # 6. Negative는 0으로 제로아웃
        "6": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["5", 0]},
        },
        # 7. 빈 잠재 이미지 (SD3 타입)
        "7": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        # 8. KSampler
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["2", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["7", 0],
            },
        },
        # 9. VAE 디코드
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["4", 0],
            },
        },
        # 10. 이미지 저장
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "z-image-turbo",
                "images": ["9", 0],
            },
        },
    }


@mcp.tool()
async def generate_image(
    prompt: str,
    width: int = 512,
    height: int = 512,
    steps: int = 8,
    cfg: float = 1.0,
    seed: int = -1,
) -> Image:
    """
    z-image-turbo 모델로 이미지를 생성합니다.

    Args:
        prompt: 생성할 이미지 설명 (영문 권장)
        width: 이미지 너비 (기본값: 512, 64의 배수)
        height: 이미지 높이 (기본값: 512, 64의 배수)
        steps: 샘플링 스텝 수 (기본값: 8)
        cfg: CFG 스케일 (기본값: 1.0)
        seed: 랜덤 시드 (-1이면 매번 랜덤)
    """
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    workflow = _build_workflow(prompt, width, height, steps, cfg, seed)

    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. ComfyUI 큐에 워크플로우 전송
        resp = await client.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
        )
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]

        # 2. 생성 완료될 때까지 폴링 (최대 10분)
        for _ in range(300):
            await asyncio.sleep(2)
            history_resp = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
            history_resp.raise_for_status()
            history = history_resp.json()

            if prompt_id not in history:
                continue

            job = history[prompt_id]

            status = job.get("status", {})
            if status.get("status_str") == "error":
                messages = status.get("messages", [])
                raise RuntimeError(f"ComfyUI 생성 오류: {messages}")

            outputs = job.get("outputs", {})
            for node_output in outputs.values():
                if "images" not in node_output:
                    continue

                image_info = node_output["images"][0]
                params = {
                    "filename": image_info["filename"],
                    "type": image_info.get("type", "output"),
                }
                if image_info.get("subfolder"):
                    params["subfolder"] = image_info["subfolder"]

                img_resp = await client.get(f"{COMFYUI_URL}/view", params=params)
                img_resp.raise_for_status()

                # PNG → JPEG 변환으로 전송 크기 최소화
                pil_img = PILImage.open(io.BytesIO(img_resp.content)).convert("RGB")
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=85)
                return Image(data=buf.getvalue(), format="jpeg")

            if outputs:
                raise RuntimeError("생성은 완료됐지만 이미지 출력을 찾을 수 없습니다.")

        raise TimeoutError("이미지 생성이 10분 내에 완료되지 않았습니다.")


if __name__ == "__main__":
    mcp.run()
