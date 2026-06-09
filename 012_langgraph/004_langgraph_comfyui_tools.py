import os
import time
import uuid
import requests
from langchain_core.tools import tool

COMFYUI_SERVER = "http://220.80.16.79:8188"
MODEL = "z_image_turbo_bf16.safetensors"
CLIP_MODEL = "qwen_3_4b.safetensors"
VAE_MODEL = "ae.safetensors"
IMAGE_SIZE = 1024
OUTPUT_DIR = "image_data"


def _build_workflow(prompt: str, seed: int) -> dict:
    return {
        "1": {"class_type": "UNETLoader",      "inputs": {"unet_name": MODEL, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",      "inputs": {"clip_name": CLIP_MODEL, "type": "lumina2"}},
        "3": {"class_type": "VAELoader",       "inputs": {"vae_name": VAE_MODEL}},
        "4": {"class_type": "CLIPTextEncode",  "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode",  "inputs": {"text": "", "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage","inputs": {"width": IMAGE_SIZE, "height": IMAGE_SIZE, "batch_size": 1}},
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["6", 0], "seed": seed,
                "steps": 4, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0,
            },
        },
        "8":  {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9":  {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "comfyui"}},
    }


def _build_img2img_workflow(prompt: str, seed: int, image_name: str, denoise: float = 0.75) -> dict:
    """참조 이미지를 기반으로 이미지를 생성하는 ComfyUI 워크플로우 (Image-to-Image)"""
    return {
        "1":  {"class_type": "UNETLoader",     "inputs": {"unet_name": MODEL, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader",     "inputs": {"clip_name": CLIP_MODEL, "type": "lumina2"}},
        "3":  {"class_type": "VAELoader",      "inputs": {"vae_name": VAE_MODEL}},
        "4":  {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5":  {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["2", 0]}},
        "6":  {"class_type": "LoadImage",      "inputs": {"image": image_name}},
        "7":  {"class_type": "VAEEncode",      "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8":  {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["7", 0], "seed": seed,
                "steps": 4, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": denoise,
            },
        },
        "9":  {"class_type": "VAEDecode",  "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage",  "inputs": {"images": ["9", 0], "filename_prefix": "comfyui_i2i"}},
    }


def _upload_image_to_comfyui(image_path: str) -> str:
    """이미지를 ComfyUI 서버에 업로드하고 서버 내 파일명을 반환"""
    filename = os.path.basename(image_path)
    ext = os.path.splitext(filename)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{COMFYUI_SERVER}/upload/image",
            files={"image": (filename, f, mime)},
            data={"overwrite": "true", "type": "input"},
            timeout=30,
        )
    resp.raise_for_status()
    result = resp.json()
    subfolder = result.get("subfolder", "")
    name = result.get("name", filename)
    return f"{subfolder}/{name}" if subfolder else name


def _save_outputs(outputs: dict) -> list:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    for node_output in outputs.values():
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
    return saved_paths


def _poll_and_download(prompt_id: str) -> list:
    for i in range(120):
        time.sleep(1)
        history = requests.get(f"{COMFYUI_SERVER}/history/{prompt_id}", timeout=10).json()
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed", False):
                print(f"[ComfyUI] 생성 완료. 출력 노드: {list(entry.get('outputs', {}).keys())}")
                return _save_outputs(entry.get("outputs", {}))
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI 실행 오류: {status.get('messages', [])}")
        if i % 10 == 0:
            print(f"[ComfyUI] 생성 대기 중... ({i}초)")
    raise TimeoutError("ComfyUI 이미지 생성 타임아웃 (120초 초과)")


def generate_text2img(prompt: str) -> str:
    """텍스트 프롬프트로 이미지를 생성하여 저장 경로를 반환"""
    seed = uuid.uuid4().int % (2**32)
    client_id = str(uuid.uuid4())
    print(f"[ComfyUI] 이미지 생성 요청: {prompt}")
    resp = requests.post(
        f"{COMFYUI_SERVER}/prompt",
        json={"prompt": _build_workflow(prompt, seed), "client_id": client_id},
        timeout=30,
    )
    if not resp.ok:
        return f"[ComfyUI] 오류 응답 ({resp.status_code}): {resp.text}"
    prompt_id = resp.json()["prompt_id"]
    print(f"[ComfyUI] 큐 등록 완료 (prompt_id: {prompt_id})")
    try:
        saved_paths = _poll_and_download(prompt_id)
    except (TimeoutError, RuntimeError) as e:
        return str(e)
    return f"이미지 생성 완료: {', '.join(saved_paths)}" if saved_paths else "이미지 생성 완료되었으나 저장된 파일이 없습니다."


def generate_img2img(prompt: str, image_path: str, denoise: float = 0.75) -> str:
    """참조 이미지와 텍스트 프롬프트를 결합하여 이미지를 생성 (Image-to-Image)"""
    try:
        image_name = _upload_image_to_comfyui(image_path)
        print(f"[ComfyUI] 참조 이미지 업로드 완료: {image_name}")
    except Exception as e:
        return f"참조 이미지 업로드 실패: {e}"

    seed = uuid.uuid4().int % (2**32)
    client_id = str(uuid.uuid4())
    print(f"[ComfyUI] 이미지투이미지 요청: {prompt} (denoise={denoise})")
    resp = requests.post(
        f"{COMFYUI_SERVER}/prompt",
        json={"prompt": _build_img2img_workflow(prompt, seed, image_name, denoise), "client_id": client_id},
        timeout=30,
    )
    if not resp.ok:
        return f"[ComfyUI] 오류 응답 ({resp.status_code}): {resp.text}"
    prompt_id = resp.json()["prompt_id"]
    print(f"[ComfyUI] 큐 등록 완료 (prompt_id: {prompt_id})")
    try:
        saved_paths = _poll_and_download(prompt_id)
    except (TimeoutError, RuntimeError) as e:
        return str(e)
    return f"이미지 생성 완료: {', '.join(saved_paths)}" if saved_paths else "이미지 생성 완료되었으나 저장된 파일이 없습니다."


# 툴스(Tools) 설정하고 사용하는 방법( 아주 많이 사용 )
# 독스트링(docstring)이 LLM에게 Tool 설명으로 전달됨
@tool
def comfyui_tools(prompt: str) -> str:
    """
    ComfyUI를 이용하여 텍스트 프롬프트로부터 이미지를 생성합니다.
    사용자가 이미지 생성, 그림 그리기, 사진 제작, 일러스트 등 시각적 콘텐츠 생성을 요청할 때 사용하세요.
    생성된 이미지는 로컬 파일로 저장되며, 저장된 파일 경로를 반환합니다.

    입력: 생성할 이미지에 대한 텍스트 설명 (영문 또는 한글 프롬프트)
    출력: 생성 완료 메시지 및 저장된 이미지 파일 경로

    입력 예시:
      - '아름다운 일몰 풍경, 황금빛 하늘, 산과 호수'
      - 'a cute cat sitting on a sofa, photorealistic, 8k quality'
      - '미래 도시의 야경, 사이버펑크 스타일, 네온사인'
      - '수채화 스타일의 봄 꽃밭, 벚꽃, 따뜻한 색감'
    """
    return generate_text2img(prompt)


@tool
def comfyui_img2img_tools(prompt: str, image_path: str, denoise: float = 0.75) -> str:
    """
    ComfyUI를 이용하여 참조 이미지와 텍스트 프롬프트를 결합해 새로운 이미지를 생성합니다 (Image-to-Image).
    기존 이미지의 구도나 스타일을 유지하면서 프롬프트 설명에 따라 내용을 변형할 때 사용하세요.
    denoise 값이 낮을수록 원본 이미지에 가깝고, 높을수록 프롬프트의 영향이 커집니다.

    입력:
      - prompt: 변형 방향을 설명하는 텍스트 (예: '수채화 스타일로 변환', 'anime style')
      - image_path: 참조할 원본 이미지의 로컬 파일 경로
      - denoise: 변형 강도 (0.0~1.0, 기본값 0.75 / 낮을수록 원본 유지)

    입력 예시:
      - prompt='oil painting style, warm tones', image_path='/path/to/photo.jpg', denoise=0.7
      - prompt='anime style illustration', image_path='/path/to/image.png', denoise=0.8
    """
    return generate_img2img(prompt, image_path, denoise)


if __name__ == "__main__":
    from typing import TypedDict, Annotated
    from dotenv import load_dotenv
    load_dotenv()

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
    TOOLS = [comfyui_tools, comfyui_img2img_tools]

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    def llm_with_tools_node(state: State):
        """LLM이 Tool 사용 여부를 결정"""
        llm_with_tools = llm.bind_tools(TOOLS)
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_use_tool(state: State) -> str:
        """마지막 메시지가 Tool 호출을 포함하면 tools로, 아니면 END"""
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            print(f"  Tool 호출: {[tc['name'] for tc in last_msg.tool_calls]}")
            return "tools"
        return "end"

    tool_node = ToolNode(TOOLS)
    graph = StateGraph(State)
    graph.add_node("llm",   llm_with_tools_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START,   "llm")
    graph.add_conditional_edges("llm", should_use_tool, {"tools": "tools", "end": END})
    graph.add_edge("tools", "llm")
    comfyui_agent = graph.compile()

    try:
        with open("graph_comfyui_tools.png", "wb") as f:
            f.write(comfyui_agent.get_graph().draw_mermaid_png())
    except Exception:
        pass

    while True:
        human_message = input("[질문(q:종료)]")
        if human_message == "q":
            exit()
        print(comfyui_agent.invoke({"messages": [human_message]}))
