import os
import sys

# Ensure the CURRENT directory (api/) is in the path so relative imports work
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.append(api_dir)

# Import app as expected by Vercel's Python runtime
# Now importing from the local web.py instead of the root
from .web import app

# Export for Vercel
# The serverless function entry point is /api/index.py.
# Vercel needs 'app' to be defined here.
app = app
