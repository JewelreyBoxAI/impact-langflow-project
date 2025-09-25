#!/usr/bin/env python3
"""
Development server runner for Impact Realty FastAPI backend
"""

import uvicorn
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(backend_dir))

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )