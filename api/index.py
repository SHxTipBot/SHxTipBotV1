import os
import sys

# Path setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import app as expected by Vercel's Python runtime
from web import app

# Export for uvicorn etc.
main = app
