import os
import time
from typing import TypedDict, Annotated

#  .env 속성 정보 가져오는 함수
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

# tools 설정하고 사용하는 방법(많이 사용)
@tool
def calculator(expression: str) -> str:
    # 독스트링(docstring)이 LLM에게 Tool 설명으로 전달됨
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

# 사용할 tools를 변수로 정의
TOOLS = [calculator, get_weather, unit_converter]

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
    with open("graph_edges_comfyui.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())
except Exception:
    pass

# 질의 응답
while True:
    human_message = input("[질문(q:종료)]")
    if human_message == "q":
        exit()

    print(manual_agent.invoke({"messages": [human_message]}))