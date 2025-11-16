#!/bin/bash

set -e

echo "Setting up Green SME Compliance Co-Pilot..."

python3 --version

echo "Creating virtual environment..."
python3 -m venv green-agent-env
source green-agent-env/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python db_init.py

echo "Creating necessary directories..."
mkdir -p templates outputs logs

echo "Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    echo "Tesseract found: $(tesseract --version | head -n 1)"
else
    echo "WARNING: Tesseract OCR not found. Install with:"
    echo "  Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  macOS: brew install tesseract"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure API keys"
echo "2. Start the API server: uvicorn main:app --reload"
echo "3. (Optional) Start Docker services: docker-compose up -d"
echo "4. (Optional) Ingest form templates: python ingest.py templates/your_form.pdf"
