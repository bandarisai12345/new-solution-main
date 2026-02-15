"""
Utilities module for Cosmetics Database Backend
"""

from .config import (
    DATABASE_PATH,
    CLEANED_CSV_PATH,
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    MAX_SQL_RESULTS,
    MAX_SEMANTIC_RESULTS
)

from .db_connections import DatabaseConnections
from .ollama_client import OllamaClient
from .vector_search import semantic_search, hybrid_search

__all__ = [
    'DATABASE_PATH',
    'CLEANED_CSV_PATH',
    'OLLAMA_MODEL',
    'EMBEDDING_MODEL',
    'PINECONE_API_KEY',
    'PINECONE_INDEX_NAME',
    'MAX_SQL_RESULTS',
    'MAX_SEMANTIC_RESULTS',
    'DatabaseConnections',
    'OllamaClient',
    'semantic_search',
    'hybrid_search'
]
