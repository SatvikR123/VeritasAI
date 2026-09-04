import logging
from langgraph.graph import StateGraph, START, END
from app.agents.state import GraphState
from app.agents.nodes import (
    collect_news,
    cluster_articles,
    summarize_clusters,
    verify_facts,
    detect_bias,
    assess_credibility,
    generate_consensus,
    compile_reports,
)

logger = logging.getLogger(__name__)

# 1. Instantiate the StateGraph with the GraphState schema
workflow = StateGraph(GraphState)

# 2. Register all 8 agent nodes
workflow.add_node("collect", collect_news)
workflow.add_node("cluster", cluster_articles)
workflow.add_node("summarize", summarize_clusters)
workflow.add_node("verify", verify_facts)
workflow.add_node("detect_bias", detect_bias)
workflow.add_node("assess_credibility", assess_credibility)
workflow.add_node("consensus", generate_consensus)
workflow.add_node("reporter", compile_reports)

# 3. Wire up the graph logic
# Start -> News Collection -> Event Clustering
workflow.add_edge(START, "collect")
workflow.add_edge("collect", "cluster")

# Sequential routing from Event Clustering through analysis agents to Consensus
workflow.add_edge("cluster", "summarize")
workflow.add_edge("summarize", "verify")
workflow.add_edge("verify", "detect_bias")
workflow.add_edge("detect_bias", "assess_credibility")
workflow.add_edge("assess_credibility", "consensus")

# Consensus Generation -> Compiled Report Generation -> Finish
workflow.add_edge("consensus", "reporter")
workflow.add_edge("reporter", END)

# 4. Compile the state graph into an executable runnable
app_graph = workflow.compile()

logger.info("LangGraph news analysis workflow compiled successfully.")
