# SHx Tip Bot Dashboard Template
# Loads the HTML at import time from the file sitting next to this script.
import os

_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
with open(_html_path, "r", encoding="utf-8") as _f:
    DASHBOARD_HTML = _f.read()
