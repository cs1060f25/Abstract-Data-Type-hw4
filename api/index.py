"""
index.py - Main API endpoint with routing for county health data queries

Attribution:
- This file was authored with generative AI assistance (Cascade). The code was reviewed and edited.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sqlite3
from typing import Any, Dict, List
from urllib.parse import urlparse

# Valid measure names
VALID_MEASURES = {
    "Violent crime rate", "Unemployment", "Children in poverty",
    "Diabetic screening", "Mammography screening", "Preventable hospital stays",
    "Uninsured", "Sexually transmitted infections", "Physical inactivity",
    "Adult obesity", "Premature Death", "Daily fine particulate matter",
}

def get_db_path() -> str:
    """Get the path to the SQLite database"""
    possible_paths = [
        "/var/task/data.db",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.db"),
        "data.db",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return possible_paths[0]

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Root API info
        if parsed_path.path in ["/api", "/api/"]:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            message = json.dumps({
                "message": "County Health Data API",
                "status": "online",
                "endpoints": {
                    "/api/county_data": "POST - Query health data by ZIP code and measure name"
                }
            })
            self.wfile.write(message.encode())
            return
        
        # Debug endpoint
        elif parsed_path.path == "/api/debug":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            info = {
                "cwd": os.getcwd(),
                "data_db_exists": os.path.exists("data.db"),
                "data_db_path": get_db_path(),
                "data_db_found": os.path.exists(get_db_path())
            }
            self.wfile.write(json.dumps(info, indent=2).encode())
            return
        
        # County data GET (show info)
        elif parsed_path.path == "/api/county_data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            message = json.dumps({
                "message": "Use POST request with JSON body",
                "required_fields": ["zip", "measure_name"]
            })
            self.wfile.write(message.encode())
            return
        
        # 404 for unknown paths
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        # Accept POST to both /api and /api/county_data
        if parsed_path.path not in ["/api", "/api/", "/api/county_data"]:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            # Check for coffee=teapot easter egg
            if body.get("coffee") == "teapot":
                self.send_response(418)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "I'm a teapot"}).encode())
                return
            
            # Validate required fields
            zip_code = body.get("zip")
            measure_name = body.get("measure_name")
            
            if not zip_code or not measure_name:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Both 'zip' and 'measure_name' are required"}).encode())
                return
            
            # Validate ZIP code format
            if not (isinstance(zip_code, str) and len(zip_code) == 5 and zip_code.isdigit()):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "ZIP code must be a 5-digit string"}).encode())
                return
            
            # Validate measure_name
            if measure_name not in VALID_MEASURES:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": f"Invalid measure_name"}).encode())
                return
            
            # Query the database
            results = query_county_data(zip_code, measure_name)
            
            # Return 404 if no results
            if not results:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": f"No data found for ZIP {zip_code} and measure '{measure_name}'"}).encode())
                return
            
            # Return results
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Invalid JSON"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"detail": f"Internal server error: {str(e)}"}).encode())
