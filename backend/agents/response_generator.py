"""
Response Generator Agent - Generates final user response
"""

from typing import Dict, List, Any, Tuple
import pandas as pd

from backend.utilities import OllamaClient
from backend.prompts import RESPONSE_GENERATOR_PROMPT


def response_generator(user_question: str, results: Dict[str, Any], explain_data: Dict[str, Any], stream: bool = False, suppress_debug: bool = True) -> Tuple[str, List[Dict]]:
    """Generate final user-friendly response with citations"""
    
    ollama_client = OllamaClient()
    
    # Prepare results summary and build citation map
    results_summary = ""
    data_summary = ""
    citation_map = {}
    citation_counter = 1
    sql_count = 0
    semantic_count = 0
    
    # Process SQL results with citations
    if "sql_results" in results and len(results['sql_results']) > 0:
        df = results['sql_results']
        sql_count = len(df)
        
        # Skip citation_id column for display
        display_cols = [col for col in df.columns if col != 'citation_id']
        results_summary += "SQL RESULTS:\n" + df[display_cols].to_string() + "\n\n"
        data_summary += f"Found {sql_count} product result(s) from database query.\n"
        
        # Create citation map for SQL results
        for idx, row in df.iterrows():
            cid = f"sql-{idx+1}"
            citation_map[cid] = {
                'type': 'sql',
                'row_index': idx + 1,
                'row_data': row.to_dict(),
                'citation_number': citation_counter
            }
            citation_counter += 1
    
    # Process semantic results with citations
    if "semantic_results" in results and len(results['semantic_results']) > 0:
        df = results['semantic_results']
        semantic_count = len(df)
        
        # Skip citation_id and unnecessary columns for display
        skip_cols = {'citation_id', 'Rank', 'Score', 'score'}
        display_cols = [col for col in df.columns if col not in skip_cols]
        results_summary += "SEMANTIC RESULTS:\n" + df[display_cols].to_string() + "\n\n"
        data_summary += f"Found {semantic_count} related result(s) from semantic search.\n"
        
        # Create citation map for semantic results
        for idx, row in df.iterrows():
            if 'citation_id' in row:
                cid = row['citation_id']
            else:
                cid = f"sem-{idx+1}"
            
            citation_map[cid] = {
                'type': 'semantic',
                'row_index': idx + 1,
                'row_data': row.to_dict(),
                'citation_number': citation_counter
            }
            citation_counter += 1
    
    if len(citation_map) == 0:
        return ("No products or data found matching your criteria. Try rephrasing your question or using different search terms.", [])
    
    # Build comprehensive data context for LLM
    data_context = f"""{data_summary}

Complete data retrieved:
{results_summary}"""

    prompt = f"""Question: {user_question}

Data Retrieved:
{data_context}

Provide a comprehensive, natural, and helpful answer that:
1. Directly addresses the user's question
2. Summarizes the key findings from the data
3. Includes specific product details (names, brands, companies, categories) when relevant
4. Is conversational and easy to understand
Feel free to reference specific data points with [1], [2], etc. for citations."""
    
    if stream:
        response = ollama_client.stream_and_collect(
            system_prompt=RESPONSE_GENERATOR_PROMPT,
            user_prompt=prompt,
            prefix="",
            suppress_debug=suppress_debug
        )
    else:
        response = ollama_client.generate_from_prompt(
            system_prompt=RESPONSE_GENERATOR_PROMPT,
            user_prompt=prompt
        )
    
    # Convert citation map to list for JSON serialization
    citation_list = []
    for cid, data in citation_map.items():
        citation_list.append({
            'citation_id': cid,
            'type': data['type'],
            'row_index': data['row_index'],
            'citation_number': data['citation_number'],
            'row_data': {k: str(v) for k, v in data['row_data'].items()} if isinstance(data['row_data'], dict) else data['row_data']
        })
    
    return response, citation_list
