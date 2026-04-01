import os
import sys

# Add the api/ directory to Python's path so we can import sibling modules
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

import traceback

try:
    # Import app using absolute import (NOT relative - Vercel doesn't support it)
    from web import app
except Exception as e:
    error_msg = traceback.format_exc()
    
    async def app(scope, receive, send):
        assert scope['type'] == 'http'
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [
                [b'content-type', b'text/html'],
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': f"<h1>Startup Error</h1><pre>{error_msg}</pre>".encode('utf-8')
        })

# Export for Vercel
app = app
