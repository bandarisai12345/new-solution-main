"""
Intent Analysis Agent - Classifies user queries
"""

import json
import re
from typing import Dict, Any

from backend.utilities import OllamaClient
from backend.prompts import INTENT_AGENT_PROMPT


def intent_agent(user_question: str, stream: bool = False, suppress_debug: bool = True) -> Dict[str, Any]:
    """Analyze user question to extract intent, entities, and classify query type"""
    
    ollama_client = OllamaClient()
    
    try:
        if stream:
            response = ollama_client.stream_and_collect(
                system_prompt=INTENT_AGENT_PROMPT,
                user_prompt=f"Question: {user_question}",
                prefix="",
                suppress_debug=suppress_debug
            )
        else:
            response = ollama_client.generate_from_prompt(
                system_prompt=INTENT_AGENT_PROMPT,
                user_prompt=f"Question: {user_question}"
            )
        
        # Extract JSON from response - strip everything outside JSON
        response = response.strip()
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        if json_match:
            intent_data = json.loads(json_match.group())
        else:
            intent_data = json.loads(response)
        
        # Ensure required fields exist
        if "query_type" not in intent_data:
            if any(word in user_question.lower() for word in ["how many", "count", "total", "top", "most"]):
                intent_data["query_type"] = "STRUCTURED"
            else:
                intent_data["query_type"] = "SEMANTIC"
        
        if "entities" not in intent_data:
            intent_data["entities"] = {}
        if "intent" not in intent_data:
            intent_data["intent"] = user_question
        
        return intent_data
        
    except Exception as e:
        # Smart default based on question keywords
        query_type = "STRUCTURED" if any(word in user_question.lower() for word in ["how many", "count", "total", "top"]) else "SEMANTIC"
        return {
            "intent": user_question,
            "entities": {},
            "query_type": query_type
        }
