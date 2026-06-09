import os
import time
import uuid
import requests
from typing import TypedDict, Annotated

# .env 속성 정보를 가져오는 함수
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 언어모델 설정
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

# 툴스(Tools) 설정하고 사용하는 방법( 아주 많이 사용 )
# 독스트링(docstring)이 LLM에게 Tool 설명으로 전달됨
@tool
def calculator(expression: str) -> str:
    """
    수학 계산을 수행합니다.
    입력 예시: '10 * 5 + 200', '100 / 4'
    """
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"계산 결과: {expression} = {result}"
    except Exception as e:
        return f"계산 오류: {str(e)}"
    
@tool
def get_weather(city: str) -> str:
    """
    도시의 현재 날씨 정보를 반환합니다.
    입력 예시: '서울', '부산', '목포', '제주'
    """
    weather_db = {
        "서울": "☀️  맑음, 22°C, 습도 45%",
        "부산": "🌥️  흐림, 19°C, 습도 70%",
        "목포": "⛅ 구름 조금, 21°C, 습도 60%",
        "제주": "🌧️  비, 17°C, 습도 90%",
    }
    return weather_db.get(city, f"'{city}'의 날씨 정보를 찾을 수 없습니다.")

@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """
    단위를 변환합니다.
    지원: km↔miles, kg↔lbs, celsius↔fahrenheit
    입력 예시: value=100, from_unit='km', to_unit='miles'
    """
    conversions = {
        ("km",       "miles"):      lambda v: v * 0.621371,
        ("miles",    "km"):         lambda v: v * 1.60934,
        ("kg",       "lbs"):        lambda v: v * 2.20462,
        ("lbs",      "kg"):         lambda v: v * 0.453592,
        ("celsius",  "fahrenheit"): lambda v: v * 9/5 + 32,
        ("fahrenheit","celsius"):   lambda v: (v - 32) * 5/9,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    return f"지원하지 않는 변환: {from_unit} → {to_unit}"

_COMFYUI_SERVER = "http://220.80.16.79:8188"
_COMFYUI_MODEL  = "z_image_turbo_bf16.safetensors"
_CLIP_MODEL     = "qwen_3_4b.safetensors"
_VAE_MODEL      = "ae.safetensors"
_IMAGE_SIZE     = 1024
_OUTPUT_DIR     = "image_data"

def _build_comfyui_workflow(prompt: str, seed: int) -> dict:
    return {
        "1": {"class_type": "UNETLoader",      "inputs": {"unet_name": _COMFYUI_MODEL, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",      "inputs": {"clip_name": _CLIP_MODEL, "type": "lumina2"}},
        "3": {"class_type": "VAELoader",       "inputs": {"vae_name": _VAE_MODEL}},
        "4": {"class_type": "CLIPTextEncode",  "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode",  "inputs": {"text": "", "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage","inputs": {"width": _IMAGE_SIZE, "height": _IMAGE_SIZE, "batch_size": 1}},
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["6", 0], "seed": seed,
                "steps": 4, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0,
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "comfyui"}},
    }

def _build_img2img_workflow(prompt: str, seed: int, image_name: str, denoise: float = 0.75) -> dict:
    return {
        "1":  {"class_type": "UNETLoader",     "inputs": {"unet_name": _COMFYUI_MODEL, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader",     "inputs": {"clip_name": _CLIP_MODEL, "type": "lumina2"}},
        "3":  {"class_type": "VAELoader",      "inputs": {"vae_name": _VAE_MODEL}},
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
    filename = os.path.basename(image_path)
    ext = os.path.splitext(filename)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{_COMFYUI_SERVER}/upload/image",
            files={"image": (filename, f, mime)},
            data={"overwrite": "true", "type": "input"},
            timeout=30,
        )
    resp.raise_for_status()
    result = resp.json()
    subfolder = result.get("subfolder", "")
    name = result.get("name", filename)
    return f"{subfolder}/{name}" if subfolder else name

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
    seed = uuid.uuid4().int % (2**32)
    client_id = str(uuid.uuid4())
    workflow = _build_comfyui_workflow(prompt, seed)

    print(f"[ComfyUI] 이미지 생성 요청: {prompt}")

    resp = requests.post(
        f"{_COMFYUI_SERVER}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30,
    )
    if not resp.ok:
        return f"[ComfyUI] 오류 응답 ({resp.status_code}): {resp.text}"
    prompt_id = resp.json()["prompt_id"]
    print(f"[ComfyUI] 큐 등록 완료 (prompt_id: {prompt_id})")

    outputs = None
    for i in range(120):
        time.sleep(1)
        history_resp = requests.get(f"{_COMFYUI_SERVER}/history/{prompt_id}", timeout=10)
        history = history_resp.json()
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed", False):
                outputs = entry.get("outputs", {})
                print(f"[ComfyUI] 생성 완료. 출력 노드: {list(outputs.keys())}")
                break
            if status.get("status_str") == "error":
                return f"ComfyUI 실행 오류: {status.get('messages', [])}"
        if i % 10 == 0:
            print(f"[ComfyUI] 생성 대기 중... ({i}초)")

    if outputs is None:
        return "ComfyUI 이미지 생성 타임아웃 (120초 초과)"

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    for node_id, node_output in outputs.items():
        for img in node_output.get("images", []):
            params = {"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "output")}
            img_resp = requests.get(f"{_COMFYUI_SERVER}/view", params=params, timeout=30)
            img_resp.raise_for_status()
            save_path = os.path.join(_OUTPUT_DIR, img["filename"])
            with open(save_path, "wb") as f:
                f.write(img_resp.content)
            saved_paths.append(save_path)
            print(f"[ComfyUI] 이미지 저장: {save_path}")

    if saved_paths:
        return f"이미지 생성 완료: {', '.join(saved_paths)}"
    return "이미지 생성 완료되었으나 저장된 파일이 없습니다."

@tool
def comfyui_img2img_tools(prompt: str, image_path: str, denoise: float = 0.75) -> str:
    """
    ComfyUI를 이용하여 참조 이미지와 텍스트 프롬프트를 결합해 새로운 이미지를 생성합니다 (Image-to-Image).
    기존 이미지의 구도나 스타일을 유지하면서 프롬프트 설명에 따라 내용을 변형할 때 사용하세요.
    denoise 값이 낮을수록 원본 이미지에 가깝고, 높을수록 프롬프트의 영향이 커집니다.

    입력:
      - prompt: 변형 방향을 설명하는 텍스트 (예: '수채화 스타일로 변환', 'anime style')
      - image_path: 참조할 원본 이미지의 로컬 파일 경로
      - denoise: 변형 강도 (0.0~1.0, 기본값 0.75)

    입력 예시:
      - prompt='oil painting style, warm tones', image_path='/path/to/photo.jpg'
      - prompt='anime style illustration', image_path='/path/to/image.png', denoise=0.8
    """
    try:
        image_name = _upload_image_to_comfyui(image_path)
        print(f"[ComfyUI] 참조 이미지 업로드 완료: {image_name}")
    except Exception as e:
        return f"참조 이미지 업로드 실패: {e}"

    seed = uuid.uuid4().int % (2**32)
    client_id = str(uuid.uuid4())
    print(f"[ComfyUI] 이미지투이미지 요청: {prompt} (denoise={denoise})")

    resp = requests.post(
        f"{_COMFYUI_SERVER}/prompt",
        json={"prompt": _build_img2img_workflow(prompt, seed, image_name, denoise), "client_id": client_id},
        timeout=30,
    )
    if not resp.ok:
        return f"[ComfyUI] 오류 응답 ({resp.status_code}): {resp.text}"
    prompt_id = resp.json()["prompt_id"]
    print(f"[ComfyUI] 큐 등록 완료 (prompt_id: {prompt_id})")

    outputs = None
    for i in range(120):
        time.sleep(1)
        history_resp = requests.get(f"{_COMFYUI_SERVER}/history/{prompt_id}", timeout=10)
        history = history_resp.json()
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed", False):
                outputs = entry.get("outputs", {})
                print(f"[ComfyUI] 생성 완료. 출력 노드: {list(outputs.keys())}")
                break
            if status.get("status_str") == "error":
                return f"ComfyUI 실행 오류: {status.get('messages', [])}"
        if i % 10 == 0:
            print(f"[ComfyUI] 생성 대기 중... ({i}초)")

    if outputs is None:
        return "ComfyUI 이미지 생성 타임아웃 (120초 초과)"

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    for node_output in outputs.values():
        for img in node_output.get("images", []):
            params = {"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "output")}
            img_resp = requests.get(f"{_COMFYUI_SERVER}/view", params=params, timeout=30)
            img_resp.raise_for_status()
            save_path = os.path.join(_OUTPUT_DIR, img["filename"])
            with open(save_path, "wb") as f:
                f.write(img_resp.content)
            saved_paths.append(save_path)
            print(f"[ComfyUI] 이미지 저장: {save_path}")

    if saved_paths:
        return f"이미지 생성 완료: {', '.join(saved_paths)}"
    return "이미지 생성 완료되었으나 저장된 파일이 없습니다."

# 사용할 툴들을 변수로 정의
TOOLS = [calculator, get_weather, unit_converter, comfyui_tools, comfyui_img2img_tools]

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
        print(f"  🔧 Tool 호출: {[tc['name'] for tc in last_msg.tool_calls]}")
        return "tools"
    return "end"

tool_node = ToolNode(TOOLS)

graph = StateGraph(State)
graph.add_node("llm",   llm_with_tools_node)
graph.add_node("tools", tool_node)
graph.add_edge(START,   "llm")
graph.add_conditional_edges("llm",   should_use_tool, {"tools": "tools", "end": END})
graph.add_edge("tools", "llm")   # Tool 실행 후 LLM으로 돌아가 최종 답변 생성

manual_agent = graph.compile()

# 그래프 구조 확인
from IPython.display import Image, display

try:
    with open("graph_manual_agent.png", "wb") as f:
        f.write(manual_agent.get_graph().draw_mermaid_png())
except Exception:
    pass

# 질의 응답
while True:
    human_message = input("[질문(q:종료)]")
    if human_message == "q":
        exit()

    print(manual_agent.invoke({"messages": [human_message]}))