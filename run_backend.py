#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to run the FastAPI backend for The Missing Link chatbot.
This can be used locally or deployed on platforms like Replit, Render, or Railway.
"""

import os
import sys
import uvicorn

# Ensure UTF-8 encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from chatbot import app

if __name__ == "__main__":
    # Get port from environment variable (for deployment platforms) or default to 8000
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting The Missing Link backend on {host}:{port}")
    print("📝 Make sure to set your GROQ_API_KEY environment variable!")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
