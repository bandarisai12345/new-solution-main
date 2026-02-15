"""
SQL Query Validator - Validates and sanitizes SQL queries
Performs security checks and ensures query safety before execution
"""

import re
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries for safety and correctness"""
    
    # List of allowed table names based on the database schema
    ALLOWED_TABLES = {
        'products',
        'ingredients',
        'product_ingredients',
        'companies',
        'brands',
        'categories',
        'cosmetics',
        'chemicals'
    }
    
    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER',
        'INSERT', 'UPDATE', 'EXEC', 'EXECUTE',
        'CREATE', 'GRANT', 'REVOKE'
    }
    
    # Safe query patterns
    SAFE_PATTERNS = [
        r'^\s*SELECT\b',  # Must start with SELECT
    ]
    
    @staticmethod
    def validate_query(sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety and correctness
        
        Args:
            sql_query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql_query or not isinstance(sql_query, str):
            return False, "Query must be a non-empty string"
        
        # Strip whitespace
        query = sql_query.strip()
        
        # Check if query starts with SELECT (read-only)
        if not re.match(r'^\s*SELECT\b', query, re.IGNORECASE):
            return False, "Only SELECT queries are allowed (read-only operations)"
        
        # Check for dangerous keywords
        upper_query = query.upper()
        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            if re.search(rf'\b{keyword}\b', upper_query):
                return False, f"Dangerous SQL keyword '{keyword}' detected - not allowed"
        
        # Check for SQL injection patterns
        injection_patterns = [
            r"['\"]\s*;",  # Quote followed by semicolon
            r"--\s*\n",    # SQL comments
            r"/\*",        # Block comments
            r"xp_",        # Extended stored procedures
            r"sp_",        # System stored procedures (risky)
            r"UNION\s+SELECT",  # Union injection
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Potential SQL injection detected - pattern: {pattern}"
        
        # Validate table names
        table_match = re.findall(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if table_match:
            for table in table_match:
                if table.lower() not in SQLValidator.ALLOWED_TABLES:
                    return False, f"Access to table '{table}' is not allowed"
        
        # Check query length (reasonable limit)
        if len(query) > 5000:
            return False, "Query exceeds maximum length (5000 characters)"
        
        return True, None
    
    @staticmethod
    def validate_results(results: list, expected_fields: Optional[list] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate query results
        
        Args:
            results: Query results (list of tuples/rows)
            expected_fields: List of expected column names
            
        Returns:
            Tuple of (is_valid, status_message, metadata)
        """
        metadata = {
            "result_count": 0,
            "is_empty": False,
            "has_nulls": False,
            "warning": None
        }
        
        if results is None:
            return False, "Results are None", metadata
        
        if not isinstance(results, list):
            return False, "Results must be a list", metadata
        
        metadata["result_count"] = len(results)
        
        if len(results) == 0:
            metadata["is_empty"] = True
            return True, "Query returned 0 results (empty result set)", metadata
        
        # Check for NULL values in results
        for row in results:
            if any(cell is None for cell in (row if isinstance(row, (list, tuple)) else row.values())):
                metadata["has_nulls"] = True
                break
        
        return True, f"Results validation passed - {len(results)} rows", metadata
    
    @staticmethod
    def sanitize_query(sql_query: str) -> str:
        """
        Sanitize SQL query string (remove comments, extra whitespace)
        
        Args:
            sql_query: Raw SQL query
            
        Returns:
            Sanitized query
        """
        # Remove SQL comments
        query = re.sub(r'--[^\n]*', '', sql_query)  # Single-line comments
        query = re.sub(r'/\*[\s\S]*?\*/', '', query)  # Block comments
        
        # Collapse multiple whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query.strip()
    
    @staticmethod
    def analyze_query_safety(sql_query: str) -> Dict[str, Any]:
        """
        Detailed safety analysis of SQL query
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            Dictionary with detailed analysis
        """
        analysis = {
            "is_select_only": False,
            "detected_tables": [],
            "detected_functions": [],
            "complexity_level": "unknown",
            "safety_score": 0,
            "warnings": []
        }
        
        upper_query = sql_query.upper()
        
        # Check if SELECT-only
        analysis["is_select_only"] = re.match(r'^\s*SELECT\b', upper_query, re.IGNORECASE) is not None
        
        # Detect table names
        tables = re.findall(r'\bFROM\s+(\w+)', upper_query, re.IGNORECASE)
        analysis["detected_tables"] = tables
        
        # Detect functions (COUNT, SUM, AVG, etc.)
        functions = re.findall(r'(\w+)\s*\(', upper_query)
        analysis["detected_functions"] = functions
        
        # Assess complexity
        join_count = len(re.findall(r'\bJOIN\b', upper_query))
        where_count = len(re.findall(r'\bWHERE\b', upper_query))
        
        if join_count > 3:
            analysis["complexity_level"] = "high"
            analysis["warnings"].append(f"Query has {join_count} JOINs - may be slow")
        elif join_count > 1 or where_count > 1:
            analysis["complexity_level"] = "medium"
        else:
            analysis["complexity_level"] = "low"
        
        # Calculate safety score
        safety_score = 100
        
        # Deduct for various factors
        if "LIKE" in upper_query:
            safety_score -= 5
            analysis["warnings"].append("Query uses LIKE operator - may be slow")
        
        if "JOIN" in upper_query:
            safety_score -= 10 * join_count
        
        if analysis["complexity_level"] == "high":
            safety_score -= 20
        
        analysis["safety_score"] = max(0, safety_score)
        
        return analysis


def validate_sql_before_execution(sql_query: str) -> Tuple[bool, Optional[str]]:
    """
    Main validation function - check SQL before execution
    
    Args:
        sql_query: SQL query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return SQLValidator.validate_query(sql_query)


def get_sql_safety_report(sql_query: str) -> Dict[str, Any]:
    """
    Get detailed safety analysis report for a SQL query
    
    Args:
        sql_query: SQL query to analyze
        
    Returns:
        Dictionary with safety analysis
    """
    is_valid, error_msg = validate_sql_before_execution(sql_query)
    analysis = SQLValidator.analyze_query_safety(sql_query)
    
    analysis["validation"] = {
        "is_valid": is_valid,
        "error_message": error_msg
    }
    
    return analysis
