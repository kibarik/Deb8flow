#!/bin/bash
# Script to run Deb8flow committee with default parameters
# Usage: ./run_committee.sh [prd_path] [question]

# Set project directory
PROJECT_DIR="/Users/aleksishmanov/projects/mad-debate-system/Deb8flow"

# Default values
DEFAULT_PRD="/Users/aleksishmanov/Downloads/МРС_vision.docx"
DEFAULT_QUESTION="What is the potential of this project?"

# Use provided arguments or defaults
PRD_PATH="${1:-$DEFAULT_PRD}"
QUESTION="${2:-$DEFAULT_QUESTION}"

# Change to project directory
cd "$PROJECT_DIR" || { echo "Failed to cd to $PROJECT_DIR"; exit 1; }

# Run the committee command
poetry run python main.py committee \
  --prd "$PRD_PATH" \
  --question "$QUESTION"
