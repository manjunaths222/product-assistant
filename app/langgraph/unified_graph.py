"""
Unified LangGraph workflow with routing between chat and analysis agents
"""

from typing import Any
from langgraph.graph import StateGraph, END
from app.langgraph.unified_state import UnifiedAgentState
from app.langgraph.nodes.router_node import create_router_node
from app.langgraph.nodes.chat_node import create_chat_node
from app.langgraph.nodes.prepare_analysis_node import create_prepare_analysis_node
from app.langgraph.nodes.analysis_adapters import (
    create_feature_analysis_adapter,
    create_feasibility_analysis_adapter
)


def create_unified_graph() -> Any:
    """
    Create and compile the unified workflow graph with routing.
    
    Returns:
        Compiled LangGraph application
    """
    # Create node functions
    router_node = create_router_node()
    prepare_analysis_node = create_prepare_analysis_node()
    chat_node = create_chat_node()
    feature_adapter = create_feature_analysis_adapter()
    feasibility_adapter = create_feasibility_analysis_adapter()
    
    # Create state graph
    workflow = StateGraph(UnifiedAgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("prepare_analysis", prepare_analysis_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("feature_analysis", feature_adapter)
    workflow.add_node("feasibility_analysis", feasibility_adapter)
    
    # Define routing logic
    def route_decision(state: UnifiedAgentState) -> str:
        """Route based on request_type determined by router"""
        request_type = state.get("request_type", "chat")
        return request_type
    
    # Define edges
    workflow.set_entry_point("router")
    
    # Router routes to appropriate agent
    # Analysis requests go through prepare_analysis first to run Codex
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "chat": "chat",
            "feature_analysis": "prepare_analysis",
            "feasibility_analysis": "prepare_analysis"
        }
    )
    
    # After preparation, route to actual analysis
    def route_after_prepare(state: UnifiedAgentState) -> str:
        """Route to analysis after preparation"""
        return state.get("request_type", "chat")
    
    workflow.add_conditional_edges(
        "prepare_analysis",
        route_after_prepare,
        {
            "feature_analysis": "feature_analysis",
            "feasibility_analysis": "feasibility_analysis",
            "chat": "chat"  # Shouldn't happen, but safety
        }
    )
    
    # All agents end after completion
    workflow.add_edge("chat", END)
    workflow.add_edge("feature_analysis", END)
    workflow.add_edge("feasibility_analysis", END)
    
    # Compile and return
    return workflow.compile()
