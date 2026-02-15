"""
Vector search functions using Pinecone and sentence transformers
"""

import pandas as pd
from typing import List, Dict, Tuple

from .db_connections import DatabaseConnections
from .config import MAX_SEMANTIC_RESULTS

# Global database connections instance
# This will be initialized in main.py
db_connections = None


def set_db_connections(connections: DatabaseConnections):
    """Set the global database connections instance"""
    global db_connections
    db_connections = connections


def semantic_search(query_text: str, top_k: int = 5, suppress_debug: bool = True) -> Tuple[pd.DataFrame, List[Dict]]:
    """Perform semantic search using Pinecone"""
    if not db_connections:
        raise RuntimeError("Database connections not initialized. Call set_db_connections() first.")
    
    if not suppress_debug:
        print(f"  Generating embedding for query...")
    # Generate embedding for query
    query_embedding = db_connections.embedding_model.encode(
        [query_text],
        normalize_embeddings=True,
        convert_to_numpy=True
    )[0]
    
    if not suppress_debug:
        print(f"  Querying vector database...")
    # Query Pinecone
    results = db_connections.pinecone_index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    
    if not suppress_debug:
        print(f"  Vector search returned {len(results.matches)} results")
    
    # Format results as DataFrame and sources
    results_data = []
    sources = []
    for i, match in enumerate(results.matches, 1):
        meta = match.metadata
        # Internal columns for backend use only
        result_row = {
            'citation_id': f"sem-{i}",  # Add citation reference (internal)
            'Rank': i,  # Internal
            'Score': f"{match.score:.4f}",  # Internal
            'Product': meta.get('product_name', 'N/A'),
            'Chemical': meta.get('chemical_name', 'N/A'),
            'CAS Number': meta.get('cas_number', 'N/A'),
            'Brand': meta.get('brand_name', 'N/A'),
            'Company': meta.get('company_name', 'N/A'),
            'Category': meta.get('sub_category', meta.get('primary_category', 'N/A')),
            'Status': 'Discontinued' if meta.get('is_discontinued') else 'Active',
            'CDPH ID': meta.get('cdph_id', 'N/A'),
        }
        results_data.append(result_row)
        
        # Add to sources list with full metadata
        sources.append({
            'type': 'semantic',
            'citation_id': f"sem-{i}",
            'rank': i,
            'score': match.score,
            'product': meta.get('product_name', 'N/A'),
            'company': meta.get('company_name', 'N/A'),
            'chemical': meta.get('chemical_name', 'N/A'),
            'cdph_id': meta.get('cdph_id', 'N/A'),
            'full_metadata': meta,
            'row_index': i
        })
    
    return pd.DataFrame(results_data), sources


def hybrid_search(semantic_query: str, sql_filter: str, top_k: int = 5, suppress_debug: bool = True) -> Tuple[pd.DataFrame, List[Dict]]:
    """Perform hybrid search combining semantic and SQL filtering"""
    if not db_connections:
        raise RuntimeError("Database connections not initialized. Call set_db_connections() first.")
    
    # Get filtered IDs from SQL using the single cosmetic_csv table
    sql = f"""
    SELECT DISTINCT CDPHId 
    FROM cosmetic_csv
    WHERE {sql_filter}
    """
    df_filtered = pd.read_sql_query(sql, db_connections.sqlite_conn)
    filtered_ids = set(df_filtered['CDPHId'].tolist())
    
    # Perform semantic search
    query_embedding = db_connections.embedding_model.encode(
        [semantic_query],
        normalize_embeddings=True,
        convert_to_numpy=True
    )[0]
    
    # Query more results to filter
    results = db_connections.pinecone_index.query(
        vector=query_embedding.tolist(),
        top_k=top_k * 10,
        include_metadata=True
    )
    
    # Filter and format results
    results_data = []
    sources = []
    citation_count = 0
    for match in results.matches:
        cdph_id = match.metadata.get('cdph_id', '')
        if cdph_id not in filtered_ids:
            continue
        
        citation_count += 1
        meta = match.metadata
        result_row = {
            'citation_id': f"hyb-{citation_count}",  # Add citation reference
            'Score': f"{match.score:.4f}",
            'Product': meta.get('product_name', 'N/A'),
            'Chemical': meta.get('chemical_name', 'N/A'),
            'Brand': meta.get('brand_name', 'N/A'),
            'Company': meta.get('company_name', 'N/A'),
            'Category': meta.get('sub_category', meta.get('primary_category', 'N/A')),
        }
        results_data.append(result_row)
        sources.append({
            'type': 'semantic_filtered',
            'citation_id': f"hyb-{citation_count}",
            'product': meta.get('product_name', 'N/A'),
            'company': meta.get('company_name', 'N/A'),
            'chemical': meta.get('chemical_name', 'N/A'),
            'full_metadata': meta,
            'row_index': citation_count
        })
        
        if len(results_data) >= top_k:
            break
    
    return pd.DataFrame(results_data), sources
