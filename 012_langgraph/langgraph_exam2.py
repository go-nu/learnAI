# 그래프의 상태에 리듀서 함수 추가하기
from typing import TypedDict, Annotated

def add(left, right):
    return left + right

class State(TypedDict):
    messages: Annotated[list[str], add]

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages

msgs1 = [HumanMessage(content="Hello", id="1")]
msgs2 = [AIMessage(content="Hi there!", id="2")]

print(add_messages(msgs1, msgs2))

msgs1 = [HumanMessage(content="Hello", id="1")]
msgs2 = [HumanMessage(content="Hello again", id="1")]

print(add_messages(msgs1, msgs2))