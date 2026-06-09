import os
import importlib.util
from typing import TypedDict, Annotated

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 003_langgraph_comfyui_node.py 라이브러리 로드
# 파일명이 숫자로 시작하므로 importlib 사용
_spec = importlib.util.spec_from_file_location(
    "comfyui_node_lib",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "003_langgraph_comfyui_node.py")
)
_comfyui_lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_comfyui_lib)

_comfyui_node = _comfyui_lib.comfyui_node
_comfyui_img2img_node = _comfyui_lib.comfyui_img2img_node

# 언어모델 설정
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")


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
        ("km",         "miles"):      lambda v: v * 0.621371,
        ("miles",      "km"):         lambda v: v * 1.60934,
        ("kg",         "lbs"):        lambda v: v * 2.20462,
        ("lbs",        "kg"):         lambda v: v * 0.453592,
        ("celsius",    "fahrenheit"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"):    lambda v: (v - 32) * 5 / 9,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    return f"지원하지 않는 변환: {from_unit} → {to_unit}"


@tool
def generate_image(prompt: str) -> str:
    """
    ComfyUI를 사용하여 텍스트 프롬프트로 이미지를 생성하고 로컬에 저장합니다.
    영문 프롬프트를 권장합니다.
    입력 예시: 'a beautiful sunset over the ocean', 'a cute cat sitting on a chair'
    """
    result = _comfyui_node({"messages": [prompt]})
    return result["messages"][-1]


@tool
def generate_image_from_image(prompt: str, image_path: str, denoise: float = 0.75) -> str:
    """
    ComfyUI를 사용하여 입력 이미지를 기반으로 새로운 이미지를 생성합니다 (Image to Image).
    입력 이미지의 구조를 유지하면서 프롬프트 방향으로 변환합니다.
    denoise: 0.0(원본 유지) ~ 1.0(완전 새 이미지), 기본값 0.75
    입력 예시: prompt='a dog in watercolor style', image_path='C:/images/input.png', denoise=0.7
    """
    result = _comfyui_img2img_node({"messages": [prompt], "image_path": image_path, "denoise": denoise})
    return result["messages"][-1]


# 사용할 tools 목록 (ComfyUI generate_image, generate_image_from_image tool 포함)
TOOLS = [calculator, get_weather, unit_converter, generate_image, generate_image_from_image]


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


if __name__ == "__main__":
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(State)
    graph.add_node("llm",   llm_with_tools_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START,   "llm")
    graph.add_conditional_edges("llm", should_use_tool, {"tools": "tools", "end": END})
    graph.add_edge("tools", "llm")

    manual_agent = graph.compile()

    try:
        with open("graph_edges_comfyui.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
    except Exception:
        pass

    while True:
        human_message = input("[질문(q:종료)] ")
        if human_message == "q":
            exit()
        print(manual_agent.invoke({"messages": [human_message]}))
