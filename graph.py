from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    parse_input,
    check_memory,
    research,
    retry_research,
    enrich,
    rank,
    book,
    save,
    send_email,
    should_retry,
    should_email,
)


def build_graph():
    g = StateGraph(AgentState)

    # Register nodes
    g.add_node("parse_input",    parse_input)
    g.add_node("check_memory",   check_memory)
    g.add_node("research",       research)
    g.add_node("retry_research", retry_research)
    g.add_node("enrich",         enrich)
    g.add_node("rank",           rank)
    g.add_node("book",           book)
    g.add_node("save",           save)
    g.add_node("send_email",     send_email)

    # Entry point
    g.set_entry_point("parse_input")

    # Linear edges
    g.add_edge("parse_input",  "check_memory")
    g.add_edge("check_memory", "research")

    # Conditional: retry research if too few results
    g.add_conditional_edges(
        "research",
        should_retry,
        {"retry": "retry_research", "enrich": "enrich"}
    )
    g.add_edge("retry_research", "enrich")

    g.add_edge("enrich", "rank")
    g.add_edge("rank",   "book")
    g.add_edge("book",   "save")

    # Conditional: email only if user provided one
    g.add_conditional_edges(
        "save",
        should_email,
        {"send_email": "send_email", "__end__": END}
    )
    g.add_edge("send_email", END)

    return g.compile()


# Compiled graph — import this in api.py
graph = build_graph()


def _initial_state(query: str) -> AgentState:
    return {
        "query":            query,
        "city":             "",
        "cuisine":          "",
        "date":             "",
        "party_size":       2,
        "vegan":            False,
        "user_email":       None,
        "past_searches":    [],
        "raw_results":      [],
        "enriched_results": [],
        "retry_count":      0,
        "recommendations":  [],
        "top_url":          "",
        "booking_status":   "",
        "email_status":     "",
        "final_answer":     "",
        "log":              [],
    }


def run_graph(query: str) -> dict:
    return graph.invoke(_initial_state(query))


def stream_graph(query: str):
    """Yields (node_name, partial_state) as each agent completes."""
    for event in graph.stream(_initial_state(query)):
        for node_name, output in event.items():
            yield node_name, output
