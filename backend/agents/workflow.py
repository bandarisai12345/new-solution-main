"""
LangGraph Workflow - Multi-agent orchestration workflow
"""

from typing import Dict, Any, Optional, Sequence, Annotated, TypedDict, List
import operator
import json
import pandas as pd

from langgraph.graph import StateGraph, END

from backend.agents.intent_agent import intent_agent
from backend.agents.sql_agent import sql_agent
from backend.agents.semantic_agent import semantic_agent
from backend.agents.response_generator import response_generator
from backend.utilities import DatabaseConnections
from backend.utilities.config import MAX_SQL_RESULTS, MAX_SEMANTIC_RESULTS


class AgentState(TypedDict):
    """State object passed between agents"""
    user_question: str
    intent_analysis: Dict[str, Any]
    sql_results: Optional[pd.DataFrame]
    semantic_results: Optional[pd.DataFrame]
    sql_sources: List[Dict]
    semantic_sources: List[Dict]
    sql_query: Optional[str]
    final_response: str
    citations: List[Dict]
    explanation: Dict[str, Any]
    messages: Annotated[Sequence[str], operator.add]
    stream: bool
    limit_results: int
    db_connections: Optional[DatabaseConnections]


def build_workflow(db_connections: DatabaseConnections):
    """Build and return the compiled LangGraph workflow"""
    
    def intent_node(state: AgentState) -> AgentState:
        """Node: Analyze user intent"""
        print("[1] INTENT ANALYSIS")
        print("-" * 40)
        intent_analysis = intent_agent(state["user_question"], stream=state.get("stream", False), suppress_debug=True)
        state["intent_analysis"] = intent_analysis
        print(f"    Query Type: {intent_analysis['query_type']}")
        if "reasoning" in intent_analysis:
            print(f"    Reasoning: {intent_analysis['reasoning'][:100]}...")
        print()
        state["messages"] = state.get("messages", []) + [f"Intent analyzed: {intent_analysis['query_type']}"]
        return state

    def sql_node(state: AgentState) -> AgentState:
        """Node: Execute SQL query"""
        print("[2] SQL AGENT")
        print("-" * 40)
        print("    Generating SQL query...")
        try:
            sql_query = sql_agent(
                state["user_question"],
                context=json.dumps(state["intent_analysis"]),
                stream=state.get("stream", False),
                suppress_debug=True
            )
            print(f"    Query: {sql_query[:80]}...")
            
            # Execute SQL
            print("    Executing query...")
            db_connections.cursor.execute(sql_query)
            results = db_connections.cursor.fetchall()
            columns = [desc[0] for desc in db_connections.cursor.description]
            df_results = pd.DataFrame(results, columns=columns)
            
            # LIMIT RESULTS FOR SMALL MODELS
            limit = state.get("limit_results", MAX_SQL_RESULTS)
            if len(df_results) > limit:
                df_results = df_results.head(limit)
            
            # Add citation IDs to results for tracking
            df_results.insert(0, 'citation_id', [f"sql-{i+1}" for i in range(len(df_results))])
            
            # Create sources with citation references
            sql_sources = []
            for idx, row in df_results.iterrows():
                sql_sources.append({
                    'type': 'sql',
                    'citation_id': f"sql-{idx+1}",
                    'row_index': idx + 1,
                    'row_data': row.to_dict(),
                    'source': 'California Safe Cosmetics Database'
                })
            
            state["sql_results"] = df_results
            state["sql_query"] = sql_query
            state["sql_sources"] = sql_sources
            print(f"    Results: {len(df_results)} rows retrieved")
            print()
            state["messages"] = state.get("messages", []) + [f"SQL executed: {len(df_results)} results"]
            
        except Exception as e:
            print(f"    ERROR: {e}")
            print()
            state["sql_results"] = pd.DataFrame()
            state["sql_query"] = None
            state["sql_sources"] = []
            state["messages"] = state.get("messages", []) + [f"SQL error: {str(e)}"]
        
        return state

    def semantic_node(state: AgentState) -> AgentState:
        """Node: Execute semantic search"""
        print("[3] SEMANTIC AGENT")
        print("-" * 40)
        print("    Searching vector database...")
        try:
            # Use limit from state, but cap at MAX_SEMANTIC_RESULTS
            limit = min(state.get("limit_results", MAX_SEMANTIC_RESULTS), MAX_SEMANTIC_RESULTS)
            df_results, sources = semantic_agent(
                state["user_question"], 
                top_k=limit, 
                sql_filter=None, 
                suppress_debug=True
            )
            
            state["semantic_results"] = df_results
            state["semantic_sources"] = sources
            print(f"    Results: {len(df_results)} documents found")
            print()
            state["messages"] = state.get("messages", []) + [f"Semantic search: {len(df_results)} results"]
        except Exception as e:
            print(f"    ERROR: {e}")
            print()
            state["semantic_results"] = pd.DataFrame()
            state["semantic_sources"] = []
            state["messages"] = state.get("messages", []) + [f"Semantic error: {str(e)}"]
        
        return state

    def response_node(state: AgentState) -> AgentState:
        """Node: Generate final response"""
        print("[4] RESPONSE GENERATION")
        print("-" * 40)
        results = {}
        if state.get("sql_results") is not None and len(state["sql_results"]) > 0:
            results["sql_results"] = state["sql_results"]
        if state.get("semantic_results") is not None and len(state["semantic_results"]) > 0:
            results["semantic_results"] = state["semantic_results"]
        
        explain_data = {
            "intent": state["intent_analysis"],
            "steps": state.get("messages", [])
        }
        
        if state.get("stream", False):
            print("    Generating response :\n")
        else:
            print("    Generating response...")
        
        final_response, citations = response_generator(
            state["user_question"],
            results,
            explain_data,
            stream=state.get("stream", False),
            suppress_debug=True
        )
        
        state["final_response"] = final_response
        state["citations"] = citations
        state["explanation"] = explain_data
        if not state.get("stream", False):
            print()
        return state

    def should_use_sql(state: AgentState) -> str:
        """Conditional edge: Check if SQL should be used based on query type"""
        query_type = state["intent_analysis"].get("query_type", "SEMANTIC")
        
        if query_type == "STRUCTURED" or query_type == "COMBINED":
            return "sql"
        return "semantic"

    def should_use_semantic(state: AgentState) -> str:
        """Conditional edge: Check if semantic should be used after SQL"""
        query_type = state["intent_analysis"].get("query_type", "SEMANTIC")
        
        if query_type == "COMBINED":
            return "semantic"
        return "response"

    # Build LangGraph workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("intent", intent_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("semantic", semantic_node)
    workflow.add_node("response", response_node)

    workflow.set_entry_point("intent")
    workflow.add_conditional_edges(
        "intent",
        should_use_sql,
        {"sql": "sql", "semantic": "semantic"}
    )
    workflow.add_conditional_edges(
        "sql",
        should_use_semantic,
        {"semantic": "semantic", "response": "response"}
    )
    workflow.add_edge("semantic", "response")
    workflow.add_edge("response", END)

    # Compile and return the graph
    return workflow.compile()
