"""
debug.py - Debug endpoint to check filesystem
"""

from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Check various paths
        info = {
            "cwd": os.getcwd(),
            "files_in_cwd": os.listdir(os.getcwd())[:20],
            "data_db_exists": os.path.exists("data.db"),
            "data_db_in_var_task": os.path.exists("/var/task/data.db"),
            "var_task_contents": os.listdir("/var/task")[:20] if os.path.exists("/var/task") else "N/A"
        }
        
        self.wfile.write(json.dumps(info, indent=2).encode())
        return
