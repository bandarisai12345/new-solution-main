"""
Cosmetics Database AI Assistant Backend
Multi-Agent RAG System with FastAPI and LangGraph
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

from .utilities import DatabaseConnections, OllamaClient
from .agents import build_workflow

__all__ = ['DatabaseConnections', 'OllamaClient', 'build_workflow']
