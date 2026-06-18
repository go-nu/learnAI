import os
from functools import partial

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from nodes.classification import decide_emotion, route_by_analysis
from nodes.quality_check import check_bad_reply, check_result, last_check, review_reply
from nodes.read_review import read_review
from nodes.reply import bad_reply, good_reply, normal_reply, regenerate_reply
from nodes.save_result import save_result
from pipeline.state import ReplyState

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)


def build_graph():
    graph = StateGraph(ReplyState)

    graph.add_node("read_review", read_review)
    graph.add_node("decide_emotion", partial(decide_emotion, llm=llm))
    graph.add_node("good_reply", partial(good_reply, llm=llm))
    graph.add_node("normal_reply", partial(normal_reply, llm=llm))
    graph.add_node("bad_reply", partial(bad_reply, llm=llm))
    graph.add_node("review_reply", partial(review_reply, llm=llm))
    graph.add_node("check_result", partial(check_result, llm=llm))
    graph.add_node("regenerate_reply", partial(regenerate_reply, llm=llm))
    graph.add_node("save_result", save_result)

    graph.add_edge(START, "read_review")
    graph.add_edge("read_review", "decide_emotion")

    graph.add_conditional_edges(
        "decide_emotion",
        route_by_analysis,
        {
            "good": "good_reply",
            "normal": "normal_reply",
            "bad": "bad_reply",
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

    return graph.compile()
