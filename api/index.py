import os
import sys

# Add the root directory to Python's path so we can import root modules
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import app using absolute import (NOT relative - Vercel doesn't support it)
from web import app

# Export for Vercel
app = app
