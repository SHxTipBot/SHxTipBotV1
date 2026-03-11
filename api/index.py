import os
import sys

# Path setup so that web.py can be found
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the FastAPI app
try:
    from web import app
except Exception as e:
    # If the app fails to import, return a simple text handler so we can see the error
    from http.server import BaseHTTPRequestHandler
    class app(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Import error: {e}'.encode('utf-8'))
            return
