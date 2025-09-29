"""
index.py - Root API endpoint
"""

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
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
