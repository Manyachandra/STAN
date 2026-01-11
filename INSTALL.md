# Installation Guide

## Quick Install (Windows)

### Option 1: Automated Setup (Recommended)

```powershell
# Run the PowerShell setup script
.\setup.ps1
```

This will:

- Check Python version
- Create virtual environment
- Install all dependencies
- Create .env configuration file
- Check Redis connection
- Create necessary directories

### Option 2: Manual Setup

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install package in development mode
pip install -e .

# 6. Create .env file
copy env.template .env
# Edit .env and add your GEMINI_API_KEY

# 7. Start Redis (using Docker)
docker run -d -p 6379:6379 --name chatbot-redis redis:7-alpine
```

## Quick Install (Linux/Mac)

### Option 1: Automated Setup (Recommended)

```bash
# Make script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install package in development mode
pip install -e .

# 6. Create .env file
cp env.template .env
# Edit .env and add your GEMINI_API_KEY

# 7. Start Redis (using Docker)
docker run -d -p 6379:6379 --name chatbot-redis redis:7-alpine
```

## Prerequisites

### Required

1. **Python 3.11+**

   ```bash
   python --version  # Should show 3.11 or higher
   ```

2. **pip** (comes with Python)

   ```bash
   pip --version
   ```

3. **Google Gemini API Key**

   - Get one at: https://ai.google.dev/
   - Free tier available

4. **Redis** (one of):
   - Docker (recommended): `docker run -d -p 6379:6379 redis:7-alpine`
   - Local install: See https://redis.io/download

### Optional

1. **Docker** (for containerized deployment)

   - Download from: https://www.docker.com/products/docker-desktop

2. **MongoDB** (for advanced analytics)
   - Docker: `docker run -d -p 27017:27017 mongo:7`
   - Local install: https://www.mongodb.com/try/download/community

## Detailed Steps

### 1. Clone or Download Project

```bash
# If using git
git clone <repository-url>
cd chatbot_system

# Or download and extract ZIP
```

### 2. Set Up Python Environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Install dev dependencies (optional, for development)
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
# Copy template
cp env.template .env  # Linux/Mac
copy env.template .env  # Windows

# Edit .env file
# Add your GEMINI_API_KEY
```

**Required configuration:**

```bash
GEMINI_API_KEY=AIzaSy...  # Your actual API key
REDIS_URL=redis://localhost:6379/0
```

### 5. Start Redis

**Using Docker (Recommended):**

```bash
docker run -d -p 6379:6379 --name chatbot-redis redis:7-alpine
```

**Verify Redis is running:**

```bash
redis-cli ping  # Should return "PONG"
```

**Or using Makefile:**

```bash
make redis
```

### 6. Verify Installation

```bash
# Check Python packages
pip list | grep chatbot

# Check configuration
python -c "import chatbot_system; print('✓ Import successful')"

# Run health check (requires API running)
python -c "from chatbot_system import ChatbotEngine; print('✓ Package working')"
```

### 7. Run First Example

```bash
# Make sure .env has GEMINI_API_KEY set
# Make sure Redis is running

python examples/basic_conversation.py
```

Expected output:

```
Initializing chatbot...
Checking system health...
Health status: {'gemini_api': True, 'redis': True, 'persona': True, 'overall': True}

==================================================
CONVERSATION START
==================================================

Bot: Hey! What's up?
...
```

## Common Issues

### Issue: "Python not found"

**Solution:** Install Python 3.11+ from https://www.python.org/downloads/

### Issue: "Module not found"

**Solution:**

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Redis connection failed"

**Solution:**

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or check if Redis is running
redis-cli ping
```

### Issue: "Gemini API error"

**Solution:**

1. Check API key is correct in `.env`
2. Verify API key has quota/credits
3. Check network connectivity

### Issue: "Permission denied" (Linux/Mac)

**Solution:**

```bash
chmod +x setup.sh
chmod +x setup.py
```

### Issue: PowerShell execution policy (Windows)

**Solution:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Verification Checklist

After installation, verify:

- [ ] Python 3.11+ installed: `python --version`
- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip list`
- [ ] Package installed: `python -c "import chatbot_system"`
- [ ] `.env` file exists with `GEMINI_API_KEY`
- [ ] Redis running: `redis-cli ping`
- [ ] Basic example runs successfully

## Using Makefile (Linux/Mac)

If you have `make` installed:

```bash
make install      # Install dependencies
make redis        # Start Redis in Docker
make run-example  # Run basic example
make run-api      # Start API server
make test         # Run tests
make help         # See all commands
```

## Docker Installation

For containerized deployment:

```bash
# Set API key
export GEMINI_API_KEY=your_key

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chatbot-api

# Stop services
docker-compose down
```

## Development Installation

For contributors and developers:

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Format code
make format

# Lint code
make lint
```

## Next Steps

After successful installation:

1. **Run Examples**: Try different examples in `examples/` directory
2. **Read Documentation**: Check QUICKSTART.md and API_REFERENCE.md
3. **Customize Persona**: Edit `config/persona.yaml`
4. **Start Building**: Integrate into your application

## Getting Help

If you encounter issues:

1. Check this documentation
2. Review error messages carefully
3. Check Redis is running: `redis-cli ping`
4. Verify `.env` configuration
5. Try running with `--verbose` flag
6. Check logs in `logs/` directory

## Uninstallation

To completely remove:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/  # Linux/Mac
rmdir /s venv  # Windows

# Remove Redis container (if using Docker)
docker stop chatbot-redis
docker rm chatbot-redis

# Remove downloaded files (optional)
cd ..
rm -rf chatbot_system/
```

---

**Last Updated:** 2026-01-10
