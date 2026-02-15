"""
Semantic Agent - Performs vector search
"""

from typing import Tuple, List, Dict
import pandas as pd

from backend.utilities import semantic_search, hybrid_search


def semantic_agent(query_text: str, top_k: int = 5, sql_filter: str = None, suppress_debug: bool = True) -> Tuple[pd.DataFrame, List[Dict]]:
    """Perform semantic search using Pinecone"""
    if not suppress_debug:
        print(f"  Searching semantic index...")
    
    if sql_filter:
        if not suppress_debug:
            print(f"    Using SQL filter")
        return hybrid_search(query_text, sql_filter, top_k, suppress_debug=suppress_debug)
    else:
        return semantic_search(query_text, top_k, suppress_debug=suppress_debug)
