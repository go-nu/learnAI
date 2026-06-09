# 라이브러리 불러오기
from typing import TypedDict, Annotated
from operator import add
# LangGraph 구현
from langgraph.graph import StateGraph, START, END

#  .env 속성 정보 가져오는 함수
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

# LangGraph State(상태정보)를 처리하는 함수
class State(TypedDict):
    messages: Annotated[list[str], add]
    question_length: int

# 그래프 시작(선언) : 그래프를 만든다 = 그래픽 빌더
graph_builder = StateGraph(State)

def guardrail(state: State) -> State:
    question_length = len(state["messages"][-1])
    return {
        "question_length": question_length
    }

# 함수를 node로 선언
graph_builder.add_node("guardrail", guardrail)

# 챗봇 노드 생성을 위한 함수 선언
def chatbot(state: State) -> State:
    question = state["messages"][-1]
    response = llm.invoke(question)
    return {
        "messages": [response.content]
    }

# LangGraph 사용할 노드는 등록
graph_builder.add_node("chatbot", chatbot)

# 조건 분기 처리 함수
def routing_function(state: State) -> str:
    if state["question_length"] > 3:
        return "chatbot"
    else:
        return END
    
# 조건을 확인하여 분기 처리하는 구조 
graph_builder.add_conditional_edges(
    "guardrail",
    routing_function,
    {"chatbot": "chatbot", END: END}
)

# 그래프 작성, 노드끼리만 연결
# conditional_edges가 guardrail과 chatbot을 연결해주긴 하나, 노드가 아닌 엣지라 그래프에 작성하지 않음
graph_builder.add_edge(START, "guardrail")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

from IPython.display import Image, display

try:
    with open("graph_edges.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())
except Exception:
    pass

# 질의 응답
while True:
    human_message = input("[질문(q:종료)]")
    if human_message =='q':
        exit()

    print(graph.invoke({"messages":[human_message]}))
