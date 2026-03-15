"""
Vercel Serverless Entry Point for Flask Application

This file serves as the entry point for Vercel's serverless environment.
It exports the Flask app for use with Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add server source to path
server_src = Path(__file__).parent.parent / 'server' / 'src'
sys.path.insert(0, str(server_src))

from server import create_app, socketio

# Create Flask app instance
app = create_app()

# Vercel requires the app to be exported
__app__ = app
