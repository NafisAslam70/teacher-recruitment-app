#!/usr/bin/env bash

# System dependencies
apt-get update
apt-get install -y tesseract-ocr poppler-utils

# Download spaCy model
python -m spacy download en_core_web_sm
