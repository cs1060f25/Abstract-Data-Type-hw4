"""
index.py - API endpoint for querying county health data by ZIP code

Attribution:
- This file was authored with generative AI assistance (Cascade). The code was reviewed and edited.
"""

import json
import os
import sqlite3
from typing import Any, Dict, List

# Valid measure names as per assignment specification
VALID_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
}


def get_db_path() -> str:
    """Get the path to the SQLite database"""
    # Try multiple possible locations
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db"),
        "/var/task/data.db",
        "data.db",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return first path as fallback
    return possible_paths[0]


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    """Convert SQLite row to dictionary with lowercase keys"""
    fields = [column[0] for column in cursor.description]
    return {field.lower(): value for field, value in zip(fields, row)}


def query_county_data(zip_code: str, measure_name: str) -> List[Dict[str, Any]]:
    """
    Query county health data for a given ZIP code and measure name.
    
    Uses parameterized queries to prevent SQL injection.
    Returns a list of matching records as dictionaries.
    """
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        raise Exception(f"Database not found at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        
        # Step 1: Look up county information from zip_county table
        cursor.execute(
            """
            SELECT county, county_state, state_abbreviation, county_code
            FROM zip_county
            WHERE zip = ?
            LIMIT 1
            """,
            (zip_code,)
        )
        
        zip_result = cursor.fetchone()
        
        if not zip_result:
            return []
        
        county_name = zip_result.get("county")
        state_abbr = zip_result.get("state_abbreviation")
        
        # Step 2: Query county_health_rankings for matching records
        cursor.execute(
            """
            SELECT *
            FROM county_health_rankings
            WHERE County = ? 
              AND State = ? 
              AND Measure_name = ?
            ORDER BY Data_Release_Year
            """,
            (county_name, state_abbr, measure_name)
        )
        
        results = cursor.fetchall()
        return results
        
    finally:
        conn.close()


def handler(event, context):
    """
    Vercel serverless function handler.
    
    Accepts JSON POST with:
    - zip: 5-digit ZIP code (required)
    - measure_name: Health measure name (required)
    - coffee: Easter egg parameter (optional)
    
    Returns:
    - 418: If coffee=teapot
    - 400: If zip or measure_name missing
    - 404: If no data found for zip/measure_name combination
    - 200: JSON array of matching health records
    """
    try:
        # Parse request
        if event.get("httpMethod") == "GET" and event.get("path") == "/api":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "message": "County Health Data API",
                    "endpoints": {
                        "/api/county_data": "POST - Query health data by ZIP code and measure name"
                    }
                })
            }
        
        # Parse body
        body_str = event.get("body", "{}")
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str
        
        # Check for coffee=teapot easter egg (supersedes all other behavior)
        if body.get("coffee") == "teapot":
            return {
                "statusCode": 418,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"detail": "I'm a teapot"})
            }
        
        # Validate required fields
        zip_code = body.get("zip")
        measure_name = body.get("measure_name")
        
        if not zip_code or not measure_name:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"detail": "Both 'zip' and 'measure_name' are required"})
            }
        
        # Validate ZIP code format (5 digits)
        if not (isinstance(zip_code, str) and len(zip_code) == 5 and zip_code.isdigit()):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"detail": "ZIP code must be a 5-digit string"})
            }
        
        # Validate measure_name is in the allowed list
        if measure_name not in VALID_MEASURES:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "detail": f"Invalid measure_name. Must be one of: {', '.join(sorted(VALID_MEASURES))}"
                })
            }
        
        # Query the database
        results = query_county_data(zip_code, measure_name)
        
        # Return 404 if no results found
        if not results:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "detail": f"No data found for ZIP {zip_code} and measure '{measure_name}'"
                })
            }
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(results)
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"detail": "Invalid JSON"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"detail": f"Internal server error: {str(e)}"})
        }
