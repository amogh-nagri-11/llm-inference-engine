#!/bin/bash
# Run gateway locally without Docker (for development)

set -e

echo "Starting LLM Inference Engine (dev mode)..."

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "ERROR: Ollama is not running. Start it with: ollama serve"
  exit 1
fi

# Install deps if venv doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r gateway/requirements.txt
else
  source venv/bin/activate
fi

# Run
WORKER_URLS=http://localhost:11434 \
API_KEY=dev-key \
DEFAULT_MODEL=llama3.1:8b \
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload