"""
Main entry point for Cosmetics Database AI Assistant
Supports both FastAPI server and CLI modes
"""

import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Ensure backend package can be found from any working directory
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import utilities
from backend.utilities import DatabaseConnections, OllamaClient
from backend.utilities.config import (
    MAX_SQL_RESULTS,
    API_HOST,
    API_PORT,
    API_RELOAD
)
from backend.utilities.vector_search import set_db_connections

# Import agents and workflow
from backend.agents import build_workflow
from backend.agents.intent_agent import intent_agent
from backend.agents.sql_agent import sql_agent
from backend.agents.semantic_agent import semantic_agent
from backend.agents.response_generator import response_generator

# ============================================================================
# GLOBAL STATE
# ============================================================================

db_connections = None
compiled_workflow = None

# ============================================================================
# PYDANTIC MODELS for FastAPI
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    question: str
    stream: bool = True
    limit_results: int = MAX_SQL_RESULTS


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str
    sql_results: Optional[List[Dict[str, Any]]] = None
    semantic_results: Optional[List[Dict[str, Any]]] = None
    sql_query_used: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    explanation: Dict[str, Any] = {}
    intent: Dict[str, Any] = {}
    routing: Dict[str, Any] = {}


# ============================================================================
# MAIN QUERY FUNCTION
# ============================================================================

def query_cosmetics_db(user_question: str, stream: bool = True, limit_results: int = MAX_SQL_RESULTS) -> Dict[str, Any]:
    """
    Query the cosmetics database using multi-agent orchestration
    
    Args:
        user_question: Natural language question
        stream: Whether to stream LLM responses
        limit_results: Maximum number of results to return
        
    Returns:
        Dict with answer, results, and explanation
    """
    global compiled_workflow, db_connections
    
    if not compiled_workflow:
        raise RuntimeError("Workflow not initialized. Call initialize() first.")
    
    # Display query header
    print("\n" + "="*80)
    print("USER QUERY")
    print("="*80)
    print(f"{user_question}")
    print("="*80 + "\n")
    
    # Initialize state
    initial_state = {
        "user_question": user_question,
        "intent_analysis": {},
        "sql_results": None,
        "semantic_results": None,
        "sql_sources": [],
        "semantic_sources": [],
        "sql_query": None,
        "final_response": "",
        "citations": [],
        "explanation": {},
        "messages": [],
        "stream": stream,
        "limit_results": min(limit_results, MAX_SQL_RESULTS),
        "db_connections": db_connections
    }
    
    # Run the workflow
    print("WORKFLOW EXECUTION\n")
    final_state = compiled_workflow.invoke(initial_state)
    print("\n" + "-"*80)
    print("Workflow execution complete.")
    print("-"*80 + "\n")
    
    # Display answer if not streaming (streaming already printed it)
    if not stream:
        print("\nANSWER\n" + "-"*80)
        print(final_state["final_response"])
        print("-"*80)
    
    # Combine sources
    all_sources = final_state.get("sql_sources", []) + final_state.get("semantic_sources", [])
    
    return {
        "answer": final_state["final_response"],
        "sql_results": final_state.get("sql_results"),
        "semantic_results": final_state.get("semantic_results"),
        "sql_query": final_state.get("sql_query"),
        "sources": all_sources,
        "citations": final_state.get("citations", []),
        "explanation": final_state["explanation"],
        "intent": final_state["intent_analysis"]
    }


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize():
    """Initialize all database connections and workflow"""
    global db_connections, compiled_workflow
    
    print("\n" + "="*80)
    print("SYSTEM INITIALIZATION")
    print("="*80 + "\n")
    
    try:
        # Initialize database connections
        print(">>> Connecting to SQLite database...")
        db_connections = DatabaseConnections()
        db_connections.connect_sqlite()
        print("    OK - SQLite connection established\n")
        
        print(">>> Connecting to Pinecone vector database...")
        db_connections.connect_pinecone()
        print("    OK - Pinecone connection established\n")
        
        print(">>> Loading embedding model...")
        db_connections.load_embedding_model()
        print("    OK - Embedding model loaded\n")
        
        # Set global db_connections for vector search module
        set_db_connections(db_connections)
        
        # Build and compile the workflow
        print(">>> Building LangGraph workflow...")
        compiled_workflow = build_workflow(db_connections)
        print("    OK - Workflow compiled\n")
        
        print("="*80)
        print("READY - System initialized successfully")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        print(f"\n----- INITIALIZATION ERROR -----")
        print(f"Error: {e}")
        print("-"*80)
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# FASTAPI APP
# ============================================================================

fastapi_app = FastAPI(
    title="Cosmetics Database AI Assistant",
    description="Multi-Agent RAG System for California Cosmetics Dataset",
    version="1.0.0"
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("\nFastAPI startup event triggered")
    initialize()


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": pd.Timestamp.now().isoformat(),
        "version": "1.0.0"
    }


@fastapi_app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Query the cosmetics database
    
    Args:
        request: QueryRequest with question and optional parameters
        
    Returns:
        QueryResponse with answer and sources
    """
    try:
        # Query database
        result = query_cosmetics_db(
            request.question,
            stream=request.stream,
            limit_results=request.limit_results
        )
        
        # Convert DataFrames to dicts for JSON serialization
        sql_results = None
        semantic_results = None
        
        if result.get("sql_results") is not None and len(result["sql_results"]) > 0:
            # Filter out internal columns
            df = result["sql_results"].copy()
            internal_cols = [col for col in ['citation_id', 'Rank', 'Score'] if col in df.columns]
            df = df.drop(columns=internal_cols, errors='ignore')
            sql_results = df.astype(str).to_dict('records')
        
        if result.get("semantic_results") is not None and len(result["semantic_results"]) > 0:
            # Filter out internal columns
            df = result["semantic_results"].copy()
            internal_cols = [col for col in ['citation_id', 'Rank', 'Score'] if col in df.columns]
            df = df.drop(columns=internal_cols, errors='ignore')
            semantic_results = df.astype(str).to_dict('records')
        
        return QueryResponse(
            answer=result["answer"],
            sql_results=sql_results,
            semantic_results=semantic_results,
            sql_query_used=None,
            sources=result.get("sources", []),
            citations=result.get("citations", []),
            explanation=result.get("explanation", {}),
            intent=result.get("intent", {}),
            routing={}
        )
    
    except Exception as e:
        print(f"Query error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@fastapi_app.get("/citation/{citation_id}")
async def get_citation_detail(citation_id: str):
    """
    Get detailed data for a specific citation
    """
    return {
        "citation_id": citation_id,
        "message": "Citation details retrieved",
        "note": "Full citation data is included in the main query response"
    }


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command line usage"""
    # Check if question provided as argument
    if len(sys.argv) < 2:
        # Interactive mode
        print("\n" + "="*80)
        print("COSMETICS DATABASE AI ASSISTANT")
        print("="*80)
        print("Natural language query interface - Type 'exit' to quit")
        print("="*80 + "\n")
        
        # Initialize system once
        if not initialize():
            sys.exit(1)
        
        # Interactive loop
        while True:
            try:
                question = input("\nEnter your question: ").strip()
                
                if not question:
                    print("Please enter a question.")
                    continue
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!\n")
                    break
                
                # Query database
                result = query_cosmetics_db(question, stream=True)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
                import traceback
                traceback.print_exc()
    else:
        # Command line mode - question passed as argument
        # Initialize system
        if not initialize():
            sys.exit(1)
        
        # Get question from command line
        question = " ".join(sys.argv[1:])
        
        # Query database
        result = query_cosmetics_db(question, stream=True)
        print("\nQuery processing complete.")


if __name__ == "__main__":
    # Check if running in FastAPI mode
    if "--fastapi" in sys.argv or "--server" in sys.argv:
        print(f"\nStarting FastAPI server on {API_HOST}:{API_PORT}...")
        uvicorn.run("backend.main:fastapi_app", host=API_HOST, port=API_PORT, reload=API_RELOAD)
    else:
        main()

