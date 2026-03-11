import os
import sys

# Add the root directory to the python path so root modules like 'web', 'database', and 'stellar_utils' can be imported
# In Vercel, the function directory is usually /var/task/api, so the root is /var/task
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the FastAPI app from the root web.py module
from web import app

# This is the entry point Vercel looks for
# Standard FastAPI on Vercel typically uses 'app' as the exported variable
