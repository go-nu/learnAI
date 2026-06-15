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

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
   temperature=0.7)

class ReplyState(TypedDict):
    # 1. 리뷰 확인
    review_id:      str
    text:           str # 리뷰
    rating:         int # 평점
    draft_text:     str
    status:         str
    revision_count: int

    # 2. 리뷰 
    def read_review(state: ReplyState):
        pass



    # LangGraph 구현
    def build_graph():
        graph = StateGraph(ReplyState)

        # 노드 생성
        graph.add_node()