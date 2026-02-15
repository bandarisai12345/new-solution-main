"""
Configuration settings for Cosmetics Database Backend
"""

import os
from pathlib import Path

# Get the backend root directory
BACKEND_ROOT = Path(__file__).parent.parent.parent

# Data Paths - pointing to data folder at root level
DATA_FOLDER = BACKEND_ROOT / "data"
DATABASE_PATH = str(DATA_FOLDER / "cosmetic_csv.db")
CLEANED_CSV_PATH = str(DATA_FOLDER / "cleaned_cosmetics.csv")
PRODUCT_EMBEDDINGS_PATH = str(DATA_FOLDER / "product_embeddings.npy")
PRODUCT_TEXTS_PATH = str(DATA_FOLDER / "product_texts.txt")

# Model Configuration
OLLAMA_MODEL = "phi3"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Pinecone Configuration
PINECONE_API_KEY = "pcsk_5F2eEr_9sX7XkAxzGc9MBDv27YiBhp98MYX8QgeXNKx1FNim58mB4mbbNNdHWcVK25nCmY"
PINECONE_INDEX_NAME = "cosmetics-rag"

# Result limiting configuration for small models
MAX_SQL_RESULTS = 6
MAX_SEMANTIC_RESULTS = 5

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# Logging Configuration
LOG_LEVEL = "INFO"
