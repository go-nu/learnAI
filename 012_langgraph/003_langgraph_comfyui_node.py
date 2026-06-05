import uuid
import json
import time
import urllib.request
import urllib.parse
import os
from datetime import datetime

COMFYUI_SERVER = "http://220.80.16.79:8188"
MODEL_NAME = "z_image_turbo_bf16.safetensors"
CLIP_NAME = "qwen_3_4b.safetensors"
VAE_NAME = "ae.safetensors"
IMAGE_SIZE = 512
# 절대경로로 지정 - Django 등 다른 디렉토리에서 임포트해도 올바른 위치에 저장
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_data")


def _build_workflow(prompt_text: str, seed: int) -> dict:
    return {
        "1": {
            "inputs": {"unet_name": MODEL_NAME, "weight_dtype": "default"},
            "class_type": "UNETLoader",
        },
        "2": {
            "inputs": {"clip_name": CLIP_NAME, "type": "qwen_image"},
            "class_type": "CLIPLoader",
        },
        "3": {
            "inputs": {"vae_name": VAE_NAME},
            "class_type": "VAELoader",
        },
        "4": {
            "inputs": {"text": prompt_text, "clip": ["2", 0]},
            "class_type": "CLIPTextEncode",
        },
        "5": {
            "inputs": {"text": "", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode",
        },
        "6": {
            "inputs": {"width": IMAGE_SIZE, "height": IMAGE_SIZE, "batch_size": 1},
            "class_type": "EmptyLatentImage",
        },
        "7": {
            "inputs": {
                "seed": seed,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
            },
            "class_type": "KSampler",
        },
        "8": {
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {"filename_prefix": "langgraph", "images": ["8", 0]},
            "class_type": "SaveImage",
        },
    }


def _get_available_nodes() -> set:
    try:
        with urllib.request.urlopen(f"{COMFYUI_SERVER}/object_info") as resp:
            return set(json.loads(resp.read()).keys())
    except Exception:
        return set()


def _queue_prompt(workflow: dict, client_id: str) -> str:
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_SERVER}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            if "error" in result:
                raise RuntimeError(f"ComfyUI 워크플로우 오류: {json.dumps(result['error'], ensure_ascii=False)}")
            return result["prompt_id"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ComfyUI API {e.code} 오류:\n{error_body}") from e


def _wait_for_completion(prompt_id: str, timeout: int = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_SERVER}/history/{prompt_id}") as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"ComfyUI 이미지 생성 타임아웃 ({timeout}초)")


def _download_image(filename: str, subfolder: str, folder_type: str, save_path: str) -> str:
    params = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type,
    })
    with urllib.request.urlopen(f"{COMFYUI_SERVER}/view?{params}") as resp:
        image_bytes = resp.read()
    with open(save_path, "wb") as f:
        f.write(image_bytes)
    return save_path


def comfyui_node(state: dict) -> dict:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    prompt_text = state["messages"][-1]
    client_id = str(uuid.uuid4())
    seed = int(time.time() * 1000) % (2 ** 32)

    print(f"[ComfyUI] 이미지 생성 시작: {prompt_text}")

    # 서버에서 사용 가능한 노드 목록 확인
    available_nodes = _get_available_nodes()
    if available_nodes:
        required_nodes = {"UNETLoader", "CLIPLoader", "VAELoader", "KSampler", "VAEDecode", "SaveImage"}
        missing = required_nodes - available_nodes
        if missing:
            print(f"[ComfyUI] 경고: 서버에 없는 노드 {missing}")
            print(f"[ComfyUI] 사용 가능한 노드 목록: {sorted(available_nodes)}")
            return {"messages": [f"ComfyUI 노드 없음: {missing} — 서버 로그 확인 필요"]}

    workflow = _build_workflow(prompt_text, seed)
    prompt_id = _queue_prompt(workflow, client_id)
    print(f"[ComfyUI] 프롬프트 큐 ID: {prompt_id}")

    history = _wait_for_completion(prompt_id)

    saved_paths = []
    for node_output in history.get("outputs", {}).values():
        for img_info in node_output.get("images", []):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            save_path = os.path.join(OUTPUT_DIR, f"comfyui_{timestamp}_{img_info['filename']}")
            _download_image(
                img_info["filename"],
                img_info.get("subfolder", ""),
                img_info.get("type", "output"),
                save_path,
            )
            saved_paths.append(save_path)
            print(f"[ComfyUI] 이미지 저장 완료: {save_path}")

    result = (
        f"이미지 생성 완료: {', '.join(saved_paths)}"
        if saved_paths
        else "이미지 생성 실패 (출력 없음)"
    )
    return {"messages": [result]}
