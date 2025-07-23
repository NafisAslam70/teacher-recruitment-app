#!/usr/bin/env bash
set -e  # Exit on any error

# Only run apt-get if it's available (Render or Linux)
if command -v apt-get &> /dev/null
then
  echo "Running on Linux - installing system packages..."
  apt-get update
  apt-get install -y gcc g++ make build-essential
  apt-get install -y tesseract-ocr poppler-utils
else
  echo "Skipping apt-get — not a Linux environment."
fi

# Download spaCy model
python -m spacy download en_core_web_sm
