#!/bin/bash
cd "$(dirname "$0")/backend"
pip install -q -r requirements.txt
exec uvicorn main:app --host 0.0.0.0 --port 3006
