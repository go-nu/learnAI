import importlib.util
from pathlib import Path
from typing import TypedDict, Annotated
from operator import add

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # 012_langgraph/
load_dotenv(ROOT_DIR / '.env')

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

# 003_langgraph_comfyui_node 동적 로드 (파일명이 숫자로 시작)
_node_path = ROOT_DIR / "003_langgraph_comfyui_node.py"
_spec = importlib.util.spec_from_file_location("comfyui_node_module", str(_node_path))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
comfyui_node = _mod.comfyui_node


class State(TypedDict):
    messages: Annotated[list[str], add]
    question_length: int


_IMAGE_KEYWORDS = ["이미지", "comfyui", "이미지생성", "image"]

graph_builder = StateGraph(State)


def guardrail(state: State) -> State:
    return {"question_length": len(state["messages"][-1])}


def chatbot(state: State) -> State:
    response = llm.invoke(state["messages"][-1])
    return {"messages": [response.content]}


def routing_function(state: State) -> str:
    last_message = state["messages"][-1].lower()
    if any(kw in last_message for kw in _IMAGE_KEYWORDS):
        return "comfyui"
    if state["question_length"] > 3:
        return "chatbot"
    return END


graph_builder.add_node("guardrail", guardrail)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("comfyui", comfyui_node)
graph_builder.add_conditional_edges(
    "guardrail",
    routing_function,
    {"chatbot": "chatbot", "comfyui": "comfyui", END: END},
)
graph_builder.add_edge(START, "guardrail")
graph_builder.add_edge("chatbot", END)
graph_builder.add_edge("comfyui", END)

graph = graph_builder.compile()


def run_graph(prompt: str) -> dict:
    return graph.invoke({"messages": [prompt]})
