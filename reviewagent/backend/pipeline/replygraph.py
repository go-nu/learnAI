import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from state import ReplyState

from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", google_api_key=api_key, temperature=0.7
)


# 1. 리뷰 읽기
def read_review(state: ReplyState) -> dict:
    pass


# 2. 리뷰 분류
def decide_emotion(state: ReplyState) -> dict:
    pass


# 3-A. 긍정 리뷰 답변
def good_reply(state: ReplyState) -> dict:
    pass


# 3-B. 보통 리뷰 답변
def normal_reply(state: ReplyState) -> dict:
    pass


# 3-C. 부정 리뷰 답변
def bad_reply(state: ReplyState) -> dict:
    pass


# 4. 부정 답변 검토
def review_reply(state: ReplyState) -> dict:
    pass


# 5. 결과 검토
def check_result(state: ReplyState) -> dict:
    pass


# 6. 답변 재생성
def regenerate_reply(state: ReplyState) -> dict:
    pass


# 7. 결과 저장
def save_result(state: ReplyState) -> dict:
    pass


# 분기 함수
def route_by_analysis(state: ReplyState) -> str:
    pass


# 부정 답변 품질 검토 라우터 (최대 2회)
def check_bad_reply(state: ReplyState) -> str:
    pass


# 답변 최종 검토 라우터 (최대 2회)
def last_check(state: ReplyState) -> str:
    pass


# LangGraph 구현
def build_graph():
    graph = StateGraph(ReplyState)

    # node 생성
    graph.add_node("read_review", read_review)
    graph.add_node("decide_emotion", decide_emotion)
    graph.add_node("good_reply", good_reply)
    graph.add_node("normal_reply", normal_reply)
    graph.add_node("bad_reply", bad_reply)
    graph.add_node("review_reply", review_reply)
    graph.add_node("check_result", check_result)
    graph.add_node("regenerate_reply", regenerate_reply)
    graph.add_node("save_result", save_result)
    # edge 연결
    graph.add_edge(START, "read_review")
    graph.add_edge("read_review", "decide_emotion")

    graph.add_conditional_edges(
        "decide_emotion",
        route_by_analysis,
        {
            "good_reply": "good_reply",
            "normal_reply": "normal_reply",
            "bad_reply": "bad_reply",
        },
    )

    graph.add_edge("good_reply", "check_result")
    graph.add_edge("normal_reply", "check_result")
    graph.add_edge("bad_reply", "review_reply")

    graph.add_conditional_edges(
        "review_reply",
        check_bad_reply,
        {
            "bad_reply": "bad_reply",
            "check_result": "check_result",
        },
    )

    graph.add_conditional_edges(
        "check_result",
        last_check,
        {
            "save_result": "save_result",
            "regenerate_reply": "regenerate_reply",
        },
    )

    graph.add_edge("regenerate_reply", "check_result")

    graph.add_edge("save_result", END)
    reply_graph = graph.compile()

    try:
        with open("reply_graph.png", "wb") as f:
            f.write(reply_graph.get_graph().draw_mermaid_png())
    except Exception:
        pass

    return reply_graph


if __name__ == "__main__":
    build_graph()
