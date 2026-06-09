# 라이브러리 불러오기
from typing import TypedDict, Annotated
from operator import add
import importlib.util
import sys

# LangGraph를 실제 제작
from langgraph.graph import StateGraph, START, END

# .env 속성 정보를 가져오는 함수
from dotenv import load_dotenv

load_dotenv()

# Gemini 언어모델 사용
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

# 003_langgraph_comfyui_node.py 동적 임포트 (숫자로 시작하는 파일명)
_spec = importlib.util.spec_from_file_location(
    "comfyui_node", "003_langgraph_comfyui_node.py"
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
generate_image = _module.generate_image


# LangGraph State(상태정보)를 처리하는 함수
class State(TypedDict):
    messages: Annotated[list[str], add]
    question_length: int


# 그래프를 시작 : 그래프를 만든다 (그래픽 빌더)
graph_builder = StateGraph(State)


def guardrail(state: State) -> State:
    question_length = len(state["messages"][-1])
    return {"question_length": question_length}


graph_builder.add_node("guardrail", guardrail)


# 챗봇 노드를 구성하기 위한 함수
def chatbot(state: State) -> State:
    question = state["messages"][-1]
    response = llm.invoke(question)
    return {"messages": [response.content]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("comfyui", generate_image)

# 이미지 생성 관련 키워드
IMAGE_KEYWORDS = ["이미지", "comfyui", "이미지생성", "image"]


# 조건에 따른 분기 처리를 위한 함수
def routing_function(state: State) -> str:
    message = state["messages"][-1].lower()
    if any(kw in message for kw in IMAGE_KEYWORDS):
        return "comfyui"
    if state["question_length"] > 3:
        return "chatbot"
    return END


# 조건을 확인하여 분기 처리하는 구조
graph_builder.add_conditional_edges(
    "guardrail",
    routing_function,
    {"chatbot": "chatbot", "comfyui": "comfyui", END: END},
)

# 그래프로 작성
graph_builder.add_edge(START, "guardrail")
graph_builder.add_edge("chatbot", END)
graph_builder.add_edge("comfyui", END)
graph = graph_builder.compile()

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

    print(graph.invoke({"messages": [human_message]}))
