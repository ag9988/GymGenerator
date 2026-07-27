#!/bin/bash
# Install dependencies
pip install -e .

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
