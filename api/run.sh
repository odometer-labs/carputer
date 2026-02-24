#!/bin/bash

VENV=".venv"

if [ -d "$VENV" ]; then
    echo "Virtual Environment found."
else
    echo "Virtual Environment not found."

    if command -v uv >/dev/null 2>&1; then
    echo "uv is installed:"
    uv --version
    else
        echo "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        uv --version
    fi
    
    echo "Creating new virtual environment..."
    uv venv --python 3.13

    source .venv/bin/activate
    uv pip install -r requirements.txt
    deactivate
fi

source .venv/bin/activate
fastapi run src/main.py