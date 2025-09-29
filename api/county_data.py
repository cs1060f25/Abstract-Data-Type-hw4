"""
county_data.py - API endpoint for querying county health data by ZIP code

Attribution:
- This file was authored with generative AI assistance (Cascade). The code was reviewed and edited.
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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


class CountyDataRequest(BaseModel):
    """Request model for county_data endpoint"""
    zip: Optional[str] = Field(None, description="5-digit ZIP code")
    measure_name: Optional[str] = Field(None, description="Health measure name")
    coffee: Optional[str] = Field(None, description="Easter egg parameter")


app = FastAPI(title="County Health Data API")


def get_db_path() -> str:
    """Get the path to the SQLite database"""
    # Look for data.db in the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data.db")
    return db_path


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
        raise HTTPException(status_code=500, detail="Database not found")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        
        # Step 1: Look up county information from zip_county table
        # Using parameterized query to prevent SQL injection
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
            # ZIP code not found
            return []
        
        county_name = zip_result.get("county")
        state_abbr = zip_result.get("state_abbreviation")
        
        # Step 2: Query county_health_rankings for matching records
        # Note: The CSV headers have mixed case (State, County, Measure_name, etc.)
        # We need to match the exact column names from the schema
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


@app.post("/county_data")
async def county_data(request: Request) -> Response:
    """
    Main endpoint for querying county health data.
    
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
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Check for coffee=teapot easter egg (supersedes all other behavior)
    if body.get("coffee") == "teapot":
        raise HTTPException(status_code=418, detail="I'm a teapot")
    
    # Validate required fields
    zip_code = body.get("zip")
    measure_name = body.get("measure_name")
    
    if not zip_code or not measure_name:
        raise HTTPException(
            status_code=400,
            detail="Both 'zip' and 'measure_name' are required"
        )
    
    # Validate ZIP code format (5 digits)
    if not (isinstance(zip_code, str) and len(zip_code) == 5 and zip_code.isdigit()):
        raise HTTPException(status_code=400, detail="ZIP code must be a 5-digit string")
    
    # Validate measure_name is in the allowed list
    if measure_name not in VALID_MEASURES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid measure_name. Must be one of: {', '.join(sorted(VALID_MEASURES))}"
        )
    
    # Query the database
    results = query_county_data(zip_code, measure_name)
    
    # Return 404 if no results found
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for ZIP {zip_code} and measure '{measure_name}'"
        )
    
    return JSONResponse(content=results)


@app.get("/")
async def root():
    """Root endpoint - provides API information"""
    return {
        "message": "County Health Data API",
        "endpoints": {
            "/county_data": "POST - Query health data by ZIP code and measure name"
        }
    }


# For Vercel serverless deployment
from mangum import Mangum
handler = Mangum(app)
