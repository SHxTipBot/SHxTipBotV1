import os
import sys

# Add the root directory to the python path so root modules like 'web' can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web import app
