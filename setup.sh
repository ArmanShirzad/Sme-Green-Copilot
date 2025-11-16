#!/bin/bash
# Green SME Compliance Co-Pilot - Setup Script
# Automated installation and initialization

set -e

echo "==============================================="
echo "Green SME Compliance Co-Pilot - Setup"
echo "==============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "green-agent-env" ]; then
    python3 -m venv green-agent-env
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source green-agent-env/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Check for Tesseract OCR
echo "Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    echo "✓ Tesseract found: $tesseract_version"
else
    echo "⚠ Tesseract not found. Install it for PDF OCR support:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi
echo ""

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠ Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p outputs
mkdir -p temp
mkdir -p templates
mkdir -p config
echo "✓ Directories created"
echo ""

# Initialize database
echo "Initializing database..."
python db_init.py
echo "✓ Database initialized"
echo ""

# Check for Docker (optional services)
echo "Checking for Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version 2>&1)
    echo "✓ Docker found: $docker_version"
    
    echo ""
    echo "Optional: Start supporting services?"
    echo "  1. MinIO (storage)"
    echo "  2. OpenWebUI (chat interface)"
    echo "  3. Skip for now"
    read -p "Enter choice (1-3): " docker_choice
    
    case $docker_choice in
        1)
            echo "Starting MinIO..."
            docker run -d -p 9000:9000 -p 9001:9001 \
                --name green-sme-minio \
                -e MINIO_ROOT_USER=minioadmin \
                -e MINIO_ROOT_PASSWORD=minioadmin \
                minio/minio server /data --console-address ":9001"
            echo "✓ MinIO started at http://localhost:9000 (console: http://localhost:9001)"
            ;;
        2)
            echo "Starting OpenWebUI..."
            docker run -d -p 3000:8080 \
                --name green-sme-openwebui \
                -v open-webui:/app/backend/data \
                ghcr.io/open-webui/open-webui:main
            echo "✓ OpenWebUI started at http://localhost:3000"
            ;;
        *)
            echo "Skipping Docker services"
            ;;
    esac
else
    echo "⚠ Docker not found. Optional services (MinIO, OpenWebUI) will not be available."
fi
echo ""

echo "==============================================="
echo "Setup Complete!"
echo "==============================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys (OpenWeather, Mistral optional)"
echo "  2. Activate environment: source green-agent-env/bin/activate"
echo "  3. Start server: python main.py"
echo "  4. Visit: http://localhost:8000"
echo "  5. API docs: http://localhost:8000/docs"
echo ""
echo "For hackathon preparation:"
echo "  - Download form templates to /templates"
echo "  - Test API endpoints with example requests"
echo "  - Configure n8n for email automation (optional)"
echo ""
echo "Happy building!"
