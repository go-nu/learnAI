import json
import time
import uuid
import os
import requests

COMFYUI_SERVER = "http://220.80.16.79:8188"
MODEL = "z_image_turbo_bf16.safetensors"
CLIP_MODEL = "qwen_3_4b.safetensors"
VAE_MODEL = "ae.safetensors"
IMAGE_SIZE = 1024
OUTPUT_DIR = "image_data"


def _build_workflow(prompt: str, seed: int) -> dict:
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": MODEL, "weight_dtype": "default"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": CLIP_MODEL, "type": "lumina2"},
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_MODEL},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["2", 0]},
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": IMAGE_SIZE, "height": IMAGE_SIZE, "batch_size": 1},
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "comfyui"},
        },
    }


def generate_image(state: dict) -> dict:
    prompt = state["messages"][-1]
    seed = uuid.uuid4().int % (2**32)
    client_id = str(uuid.uuid4())
    workflow = _build_workflow(prompt, seed)

    print(f"[ComfyUI] 이미지 생성 요청: {prompt}")

    resp = requests.post(
        f"{COMFYUI_SERVER}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30,
    )
    if not resp.ok:
        print(f"[ComfyUI] 오류 응답 ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    prompt_id = resp.json()["prompt_id"]
    print(f"[ComfyUI] 큐 등록 완료 (prompt_id: {prompt_id})")

    outputs = None
    for i in range(120):
        time.sleep(1)
        history_resp = requests.get(f"{COMFYUI_SERVER}/history/{prompt_id}", timeout=10)
        history = history_resp.json()
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            # completed: true 가 될 때까지 대기
            if status.get("completed", False):
                outputs = entry.get("outputs", {})
                print(f"[ComfyUI] 생성 완료. 출력 노드: {list(outputs.keys())}")
                break
            # 서버 측 실행 오류 확인
            if status.get("status_str") == "error":
                err_msgs = status.get("messages", [])
                raise RuntimeError(f"ComfyUI 실행 오류: {err_msgs}")
        if i % 10 == 0:
            print(f"[ComfyUI] 생성 대기 중... ({i}초)")

    if outputs is None:
        raise TimeoutError("ComfyUI 이미지 생성 타임아웃 (120초 초과)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved_paths = []

    for node_id, node_output in outputs.items():
        for img in node_output.get("images", []):
            params = {
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            }
            img_resp = requests.get(f"{COMFYUI_SERVER}/view", params=params, timeout=30)
            img_resp.raise_for_status()

            save_path = os.path.join(OUTPUT_DIR, img["filename"])
            with open(save_path, "wb") as f:
                f.write(img_resp.content)
            saved_paths.append(save_path)
            print(f"[ComfyUI] 이미지 저장: {save_path}")

    if saved_paths:
        result_msg = f"이미지 생성 완료: {', '.join(saved_paths)}"
    else:
        result_msg = "이미지 생성 완료되었으나 저장된 파일이 없습니다."

    return {"messages": [result_msg]}
