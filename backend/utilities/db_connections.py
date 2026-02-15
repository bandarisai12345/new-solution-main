"""
Database connection management for SQLite and Pinecone
"""

import sqlite3
import os
import pandas as pd
from pathlib import Path

# Suppress HuggingFace Hub warnings
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'

# Suppress transformers library warnings and logging
import warnings
warnings.filterwarnings('ignore')

from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

from .config import (
    DATABASE_PATH,
    CLEANED_CSV_PATH,
    EMBEDDING_MODEL,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME
)


class DatabaseConnections:
    """Manages connections to SQLite and Pinecone"""
    
    def __init__(self):
        self.sqlite_conn = None
        self.cursor = None
        self.pinecone_index = None
        self.embedding_model = None
    
    def connect_sqlite(self, db_path: str = DATABASE_PATH):
        """Connect to SQLite database and load CSV if needed"""
        print(f"  Connecting to SQLite database...")
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.sqlite_conn = sqlite3.connect(db_path)
        self.cursor = self.sqlite_conn.cursor()
        
        # Check if cosmetic_csv table exists and has data
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cosmetic_csv'"
        )
        table_exists = self.cursor.fetchone()
        
        if table_exists:
            self.cursor.execute("SELECT COUNT(*) FROM cosmetic_csv")
            count = self.cursor.fetchone()[0]
            if count > 0:
                print(f"    SQLite database connected ({count:,} rows)")
                return self.cursor
        
        # Load CSV into database
        print(f"    Loading CSV data into database...")
        self._load_csv_to_database()
        
        return self.cursor
    
    def _load_csv_to_database(self):
        """Load the cleaned CSV into a single table"""
        if not os.path.exists(CLEANED_CSV_PATH):
            raise FileNotFoundError(f"Cleaned CSV not found: {CLEANED_CSV_PATH}")
        
        print(f"    Reading CSV: {CLEANED_CSV_PATH}")
        # Try multiple encodings due to potential encoding issues
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(CLEANED_CSV_PATH, encoding=encoding)
                print(f"    CSV read with {encoding} encoding")
                break
            except (UnicodeDecodeError, LookupError) as e:
                continue
        
        if df is None:
            raise ValueError(f"Could not read CSV with any of the encodings: {encodings}")
        
        # Load into SQLite
        df.to_sql('cosmetic_csv', self.sqlite_conn, if_exists='replace', index=False)
        
        # Create indexes for better query performance
        print(f"    Creating indexes...")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chemical_name ON cosmetic_csv(ChemicalName)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_company_name ON cosmetic_csv(CompanyName)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_brand_name ON cosmetic_csv(BrandName)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_product_name ON cosmetic_csv(ProductName)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_primary_category ON cosmetic_csv(PrimaryCategory)"
        )
        self.sqlite_conn.commit()
        
        print(f"    Loaded {len(df):,} rows into cosmetic_csv table")
        print(f"    Created performance indexes")
    
    def connect_pinecone(self):
        """Connect to Pinecone index"""
        print(f"\n  Connecting to Pinecone index: {PINECONE_INDEX_NAME}")
        
        pc = Pinecone(api_key=PINECONE_API_KEY)
        self.pinecone_index = pc.Index(PINECONE_INDEX_NAME)
        
        # Get index stats
        stats = self.pinecone_index.describe_index_stats()
        print(f"    Pinecone connected ({stats.total_vector_count:,} vectors)")
        
        return self.pinecone_index
    
    def load_embedding_model(self):
        """Load sentence transformer model"""
        from io import StringIO
        import sys
        
        # Suppress all output during model loading
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        finally:
            sys.stdout = old_stdout
        
        return self.embedding_model
