# PowerShell setup script for chatbot system (Windows)
# Run this to set up the project on a new Windows system

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Chatbot System - Setup Script (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1 | Select-String -Pattern "(\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    Write-Host "✓ Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11 or higher" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
Write-Host "✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Install package in development mode
Write-Host "Installing chatbot_system package..." -ForegroundColor Yellow
pip install -e .
Write-Host "✓ Package installed" -ForegroundColor Green
Write-Host ""

# Create .env file if it doesn't exist
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
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
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host "⚠ Please edit .env and add your GEMINI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists" -ForegroundColor Yellow
}
Write-Host ""

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Yellow
try {
    $redisCheck = redis-cli ping 2>&1
    if ($redisCheck -like "*PONG*") {
        Write-Host "✓ Redis is running" -ForegroundColor Green
    } else {
        throw "Redis not responding"
    }
} catch {
    Write-Host "⚠ Redis is not running or not installed" -ForegroundColor Yellow
    Write-Host "Start Redis using Docker:" -ForegroundColor Yellow
    Write-Host "docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Cyan
}
Write-Host ""

# Create logs directory
Write-Host "Creating logs directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
Write-Host "✓ logs/ directory created" -ForegroundColor Green
Write-Host ""

# Run tests (optional)
$runTests = Read-Host "Would you like to run tests? (y/n)"
if ($runTests -eq "y" -or $runTests -eq "Y") {
    Write-Host "Running tests..." -ForegroundColor Yellow
    pytest tests/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Some tests failed (this is expected if Redis is not running)" -ForegroundColor Yellow
    }
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env and add your GEMINI_API_KEY"
Write-Host "2. Start Redis if not running:"
Write-Host "   docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Cyan
Write-Host "3. Run a basic example:"
Write-Host "   python examples\basic_conversation.py" -ForegroundColor Cyan
Write-Host "4. Or start the API server:"
Write-Host "   python examples\api_server.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "- Quick Start: QUICKSTART.md"
Write-Host "- API Reference: API_REFERENCE.md"
Write-Host "- Deployment: DEPLOYMENT.md"
Write-Host ""
Write-Host "Happy chatting! 🤖✨" -ForegroundColor Green

