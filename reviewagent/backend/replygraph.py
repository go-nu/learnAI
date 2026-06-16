import json
import os
import re
import subprocess
import sys
import time
from typing import TypedDict, Annotated, List, Optional, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END


from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=api_key,
    temperature=0.7)

class ReplyState(TypedDict):
    review_id       : int
    text            : str           # 리뷰
    rating          : int           # 평점
    sentiment_score : float         # 분석 결과 (-1.0 ~ 1.0)
    sentiment_label : str           # good / normal / bad
    category        : str           # 감정 판단 사유
    route           : str           # 분기 경로
    draft_text      : str           # AI 답변 초안
    revision_count  : int           # 재생성 횟수
    tags            : list[str]     # 키워드 리스트

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

# 5. 관리자 검토
def admin_check(state: ReplyState) -> dict:
    pass

# 6. 결과 저장
def save_result(state: ReplyState) -> dict:
    pass


# 분기 함수
def route_by_analysis(state: ReplyState) -> dict:
    pass

# 부정 답변 품질 검토 라우터
def check_bad_reply(state: ReplyState) -> str:
    pass

# LangGraph 구현
def build_graph():
    graph = StateGraph(ReplyState)

    # node 생성
    graph.add_node('read_review', read_review)
    graph.add_node('decide_emotion', decide_emotion)
    graph.add_node('good_reply', good_reply)
    graph.add_node('normal_reply', normal_reply)
    graph.add_node('bad_reply', bad_reply)
    graph.add_node('review_reply', review_reply)
    graph.add_node('admin_check', admin_check)
    graph.add_node('save_result', save_result)

    # edge 연결
    graph.add_edge(START, 'read_review')
    graph.add_edge('read_review', 'decide_emotion')
    graph.add_conditional_edges(
        'decide_emotion',
        route_by_analysis,
        {
            'good_reply':   'good_reply',
            'normal_reply': 'normal_reply',
            'bad_reply':    'bad_reply'
        },
    )
    graph.add_edge('good_reply', 'save_result')
    graph.add_edge('normal_reply', 'save_result')
    graph.add_edge('bad_reply', 'review_reply')
    graph.add_conditional_edges(
        'review_reply',
        check_bad_reply,
        {
            'bad_reply':   'bad_reply',
        },
    )
    graph.add_edge('review_reply', 'admin_check')
    graph.add_edge('admin_check', 'save_result')
    graph.add_edge('save_result', END)

    reply_graph = graph.compile()

    # 그래프 구조 확인
    from IPython.display import Image, display

    try:
        with open("reply_graph.png", "wb") as f:
            f.write(reply_graph.get_graph().draw_mermaid_png())
    except Exception:
        pass

    return reply_graph


if __name__ == "__main__":
    build_graph()
