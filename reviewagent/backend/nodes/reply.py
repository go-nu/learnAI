import json

from pipeline.state import ReplyState
from nodes.utils import get_text


# 마크다운 제거 로직
def delete_markdown(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


# 좋은 리뷰에 대한 답변 생성
def good_reply(state: ReplyState, llm) -> dict:
    prompt = f"""
다음 쇼핑몰 리뷰에 대한 판매자의 답변을 생성하세요.

별점: {state["rating"]}
리뷰: {state["text"]}

답변 조건:
- 구조: 감사 인사 + 재구매 유도
- 분량: 2~3문장
- 어조: 친절하고 따뜻하게

아래 JSON 형식으로만 출력하세요. 다른 텍스트는 쓰지 마세요.
{{
  "reply_text": "답변 내용",
  "tags": ["키워드1", "키워드2"]
}}

tags는 리뷰 본문에서 언급된 핵심 키워드 2~5개를 추출하세요. (예: 배송, 포장, 가성비, 품질)
"""

    response = llm.invoke(prompt)
    raw = get_text(response)
    print(f"[good_reply] LLM 원문:\n{raw}\n")
    result = json.loads(delete_markdown(raw))

    return {
        "reply_text": result["reply_text"],
        "tags": result.get("tags", []),
    }


# 보통 리뷰에 대한 답변 생성
def normal_reply(state: ReplyState, llm) -> dict:
    prompt = f"""
다음 쇼핑몰 리뷰에 대한 판매자의 답변을 생성하세요.

별점: {state["rating"]}
리뷰: {state["text"]}

답변 조건:
- 구조: 감사 인사 + 개선 약속
- 분량: 2~3문장
- 어조: 진심 어린 태도로 개선 의지를 전달

아래 JSON 형식으로만 출력하세요. 다른 텍스트는 쓰지 마세요.
{{
  "reply_text": "답변 내용",
  "tags": ["키워드1", "키워드2"]
}}

tags는 리뷰 본문에서 언급된 핵심 키워드 2~5개를 추출하세요. (예: 배송, 포장, 가성비, 품질)
"""

    response = llm.invoke(prompt)
    raw = get_text(response)
    print(f"[normal_reply] LLM 원문:\n{raw}\n")
    result = json.loads(delete_markdown(raw))

    return {
        "reply_text": result["reply_text"],
        "tags": result.get("tags", []),
    }


# 나쁜 리뷰에 대한 답변 생성
def bad_reply(state: ReplyState, llm) -> dict:
    retry = state["retry_count"]
    retry_guide = "\n이전 답변이 품질 기준에 미달했습니다. 공감, 사과, 해결책을 더 구체적으로 작성하세요." if retry > 0 else ""

    prompt = f"""
다음 쇼핑몰 리뷰에 대한 판매자의 답변을 생성하세요.{retry_guide}

별점: {state["rating"]}
리뷰: {state["text"]}

답변 조건:
- 구조: 공감 + 사과 + 해결책 (3단 구성 필수)
- 분량: 3~4문장
- 어조: 진심 어린 사과와 구체적인 해결 의지 전달

아래 JSON 형식으로만 출력하세요. 다른 텍스트는 쓰지 마세요.
{{
  "reply_text": "답변 내용",
  "tags": ["키워드1", "키워드2"]
}}

tags는 리뷰 본문에서 언급된 핵심 키워드 2~5개를 추출하세요. (예: 배송, 포장, 가성비, 품질)
"""

    response = llm.invoke(prompt)
    raw = get_text(response)
    print(f"[bad_reply] LLM 원문:\n{raw}\n")
    result = json.loads(delete_markdown(raw))

    return {
        "reply_text": result["reply_text"],
        "tags": result.get("tags", []),
    }


# 마지막 답변 재생성 노드
def regenerate_reply(state: ReplyState, llm) -> dict:
    prompt = f"""
아래 쇼핑몰 리뷰 답변이 품질 기준에 미달했습니다. 더 자연스럽고 구체적으로 재작성하세요.

원본 리뷰: {state["text"]}
기존 답변: {state["reply_text"]}

재작성 조건:
- 기존 답변의 구조(감사/공감/사과/해결책)는 유지하되 표현을 개선
- 분량: 2~4문장
- 어조: 자연스럽고 진심이 느껴지게

reply_text 값만 아래 JSON 형식으로 출력하세요. 다른 텍스트는 쓰지 마세요.
{{
  "reply_text": "재작성된 답변"
}}
"""

    response = llm.invoke(prompt)
    raw = get_text(response)
    print(f"[regenerate_reply] LLM 원문:\n{raw}\n")
    result = json.loads(delete_markdown(raw))

    return {
        "reply_text": result["reply_text"],
        "regenerate_count": state["regenerate_count"] + 1,
    }
