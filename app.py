"""
app.py - Flask API for county health data queries
Optimized for Render deployment

Attribution:
- This file was authored with generative AI assistance (Cascade). The code was reviewed and edited.
"""

from flask import Flask, request, jsonify
import os
import sqlite3
from typing import Any, Dict, List

app = Flask(__name__)

# Valid measure names
VALID_MEASURES = {
    "Violent crime rate", "Unemployment", "Children in poverty",
    "Diabetic screening", "Mammography screening", "Preventable hospital stays",
    "Uninsured", "Sexually transmitted infections", "Physical inactivity",
    "Adult obesity", "Premature Death", "Daily fine particulate matter",
}

def get_db_path() -> str:
    """Get the path to the SQLite database"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    """Convert SQLite row to dictionary with lowercase keys"""
    fields = [column[0] for column in cursor.description]
    return {field.lower(): value for field, value in zip(fields, row)}

def query_county_data(zip_code: str, measure_name: str) -> List[Dict[str, Any]]:
    """Query county health data"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise Exception(f"Database not found at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT county, state_abbreviation FROM zip_county WHERE zip = ? LIMIT 1",
            (zip_code,)
        )
        zip_result = cursor.fetchone()
        if not zip_result:
            return []
        
        cursor.execute(
            "SELECT * FROM county_health_rankings WHERE County = ? AND State = ? AND Measure_name = ? ORDER BY Data_Release_Year",
            (zip_result["county"], zip_result["state_abbreviation"], measure_name)
        )
        return cursor.fetchall()
    finally:
        conn.close()

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "County Health Data API",
        "endpoints": {
            "/county_data": "POST - Query health data by ZIP code and measure name"
        }
    })

@app.route('/county_data', methods=['GET', 'POST'])
def county_data():
    """Main endpoint for querying county health data"""
    
    if request.method == 'GET':
        return jsonify({
            "message": "Use POST request with JSON body",
            "required_fields": ["zip", "measure_name"]
        })
    
    # POST request
    try:
        body = request.get_json()
        
        # Check for coffee=teapot easter egg
        if body and body.get("coffee") == "teapot":
            return jsonify({"detail": "I'm a teapot"}), 418
        
        # Validate required fields
        if not body:
            return jsonify({"detail": "Request body must be JSON"}), 400
        
        zip_code = body.get("zip")
        measure_name = body.get("measure_name")
        
        if not zip_code or not measure_name:
            return jsonify({"detail": "Both 'zip' and 'measure_name' are required"}), 400
        
        # Validate ZIP code format
        if not (isinstance(zip_code, str) and len(zip_code) == 5 and zip_code.isdigit()):
            return jsonify({"detail": "ZIP code must be a 5-digit string"}), 400
        
        # Validate measure_name
        if measure_name not in VALID_MEASURES:
            return jsonify({"detail": f"Invalid measure_name"}), 400
        
        # Query the database
        results = query_county_data(zip_code, measure_name)
        
        # Return 404 if no results
        if not results:
            return jsonify({"detail": f"No data found for ZIP {zip_code} and measure '{measure_name}'"}), 404
        
        # Return results
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({"detail": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
