import os
import sys

# Add the api/ directory to Python's path so we can import sibling modules
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

# Import app using absolute import (NOT relative - Vercel doesn't support it)
from web import app

# Export for Vercel
app = app
