#!/bin/bash

# Change to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Run the MCP server
python main.py
