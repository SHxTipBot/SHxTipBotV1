# Vercel entrypoint at the root level
import logging
import sys
import os

from web import app

# Expose app for Vercel
main = app
