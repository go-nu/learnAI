from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

from typing import TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph

class State(TypedDict):
    messages: Annotated[list[str], add]

graph = StateGraph(State)

def chatbot(state: State): # [ 1 ]
    question = state["messages"]
    answer = f"사용자 입력을 그대로 반환하는 챗봇입니다. {question} 라는 질문을 받았습니다." # [ 2 ]
    return {"messages": [answer]} # [ 3 ]

print(graph.add_node("chatbot", chatbot))

# 그래프에 조건부 엣지 추가하기
from langgraph.graph import START, END

graph.add_edge(START, "chatbot")
print(graph.add_edge("chatbot", END))

graph1 = graph.compile()

try:
    with open("graph.png", "wb") as f:
        f.write(graph1.get_graph().draw_mermaid_png())
except Exception:
    pass