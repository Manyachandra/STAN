#!/bin/bash
# Setup script for chatbot system
# Run this to set up the project on a new system

set -e  # Exit on error

echo "=========================================="
echo "Chatbot System - Setup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo -e "${RED}Error: Python $required_version or higher is required${NC}"
    echo "Current version: $python_version"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
else
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Install package in development mode
echo "Installing chatbot_system package..."
pip install -e .
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# MongoDB Configuration (Optional)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chatbot_memory

# System Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MAX_TOKENS_PER_REQUEST=2048

# Paths
PERSONA_CONFIG=config/persona.yaml
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env and add your GEMINI_API_KEY${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi
echo ""

# Check Redis
echo "Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠ Redis is not running${NC}"
        echo "Start Redis with: redis-server"
        echo "Or using Docker: docker run -d -p 6379:6379 redis:7-alpine"
    fi
else
    echo -e "${YELLOW}⚠ redis-cli not found${NC}"
    echo "Install Redis or use Docker: docker run -d -p 6379:6379 redis:7-alpine"
fi
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs
echo -e "${GREEN}✓ logs/ directory created${NC}"
echo ""

# Run tests (optional)
echo "Would you like to run tests? (y/n)"
read -r run_tests
if [[ "$run_tests" == "y" || "$run_tests" == "Y" ]]; then
    echo "Running tests..."
    pytest tests/ -v || echo -e "${YELLOW}Some tests failed (this is expected if Redis is not running)${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY"
echo "2. Start Redis if not running:"
echo "   docker run -d -p 6379:6379 redis:7-alpine"
echo "3. Run a basic example:"
echo "   python examples/basic_conversation.py"
echo "4. Or start the API server:"
echo "   python examples/api_server.py"
echo ""
echo "Documentation:"
echo "- Quick Start: QUICKSTART.md"
echo "- API Reference: API_REFERENCE.md"
echo "- Deployment: DEPLOYMENT.md"
echo ""
echo "Happy chatting! 🤖✨"

