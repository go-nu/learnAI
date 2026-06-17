from pipeline.state import ReplyState


def decide_emotion(state: ReplyState, llm) -> dict:
    prompt = f"""
        다음 쇼핑몰 리뷰의 감성을 분류하세요.
        별점: {state["rating"]}
        리뷰: {state["text"]}

        good, normal, bad 중 하나만 답하세요.
    """

    response = llm.invoke(prompt)

    label = response.content.strip.lower()

    if label not in ("good", "normal", "bad"):
        label = "normal"

    return {
        "emotion_label": label,
    }


def route_by_analysis(state: ReplyState) -> str:
    return state["emotion_label"]
