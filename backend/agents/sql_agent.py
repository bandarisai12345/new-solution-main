"""
SQL Agent - Generates SQL queries from natural language
"""

import json
from typing import Optional

from backend.utilities import OllamaClient
from backend.prompts import SQL_AGENT_PROMPT


def sql_agent(user_question: str, context: str = "", stream: bool = False, suppress_debug: bool = True) -> str:
    """Generate SQL query from natural language"""
    
    ollama_client = OllamaClient()
    
    if not suppress_debug:
        print(f"\n💾 SQL Agent generating query...")
    
    # Build focused prompt
    if context:
        try:
            context_data = json.loads(context)
            entities = context_data.get('entities', {})
            chemicals = entities.get('chemicals', [])
            companies = entities.get('companies', [])
            brands = entities.get('brands', [])
            
            hints = []
            if chemicals:
                hints.append(f"Looking for ingredients: {', '.join(chemicals)}")
            if companies:
                hints.append(f"Filtering by companies: {', '.join(companies)}")
            if brands:
                hints.append(f"Filtering by brands: {', '.join(brands)}")
            
            prompt = f"{user_question}\n\nContext: {' '.join(hints)}" if hints else user_question
        except:
            prompt = user_question
    else:
        prompt = user_question
    
    if stream:
        if not suppress_debug:
            print("   🔨 SQL: ", end='', flush=True)
        response = ollama_client.stream_and_collect(
            system_prompt=SQL_AGENT_PROMPT,
            user_prompt=prompt,
            prefix="",
            suppress_debug=suppress_debug
        )
    else:
        response = ollama_client.generate_from_prompt(
            system_prompt=SQL_AGENT_PROMPT,
            user_prompt=prompt
        )
    
    # Extract SQL query
    sql_query = response.strip()
    sql_query = sql_query.replace('```sql', '').replace('```', '').replace('```', '').strip()
    
    # Find SELECT statement
    if 'SELECT' in sql_query.upper():
        start_idx = sql_query.upper().find('SELECT')
        sql_query = sql_query[start_idx:]
        # Remove any text after the query
        if ';' in sql_query:
            sql_query = sql_query[:sql_query.find(';') + 1]
    
    if not suppress_debug:
        print(f"  SQL Query: {sql_query[:100]}..." if len(sql_query) > 100 else f"  SQL Query: {sql_query}")
    return sql_query
