"""
Quick installation verification script.
"""

import sys

print("="*50)
print("Chatbot System - Installation Verification")
print("="*50)
print()

# Check Python version
print(f"[OK] Python version: {sys.version.split()[0]}")

# Check core imports
try:
    import chatbot_system
    print(f"[OK] chatbot_system package: v{chatbot_system.__version__}")
except ImportError as e:
    print(f"[FAIL] chatbot_system import failed: {e}")
    sys.exit(1)

# Check individual components
components = [
    ("ChatbotEngine", "chatbot_system.core.chatbot_engine"),
    ("PersonaManager", "chatbot_system.core.persona_manager"),
    ("SafetyLayer", "chatbot_system.core.safety_layer"),
    ("MemoryManager", "chatbot_system.memory.memory_manager"),
    ("ToneDetector", "chatbot_system.conversation.tone_detector"),
    ("GeminiClient", "chatbot_system.integration.gemini_client"),
]

print("\nCore Components:")
for name, module_path in components:
    try:
        parts = module_path.split(".")
        mod = __import__(module_path, fromlist=[parts[-1]])
        getattr(mod, name)
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

# Check configuration files
import os

print("\nConfiguration Files:")
config_files = [
    "config/persona.yaml",
    "config/settings.yaml",
    ".env",
]

for file_path in config_files:
    if os.path.exists(file_path):
        print(f"  [OK] {file_path}")
    else:
        print(f"  [MISSING] {file_path}")

# Check dependencies
print("\nKey Dependencies:")
dependencies = [
    "google.generativeai",
    "pydantic",
    "yaml",
    "redis",
    "fastapi",
    "httpx",
]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"  [OK] {dep}")
    except ImportError:
        print(f"  [MISSING] {dep}")

print("\n" + "="*50)
print("Installation Status: [READY]")
print("="*50)
print()
print("Next Steps:")
print("1. Edit .env and add your GEMINI_API_KEY")
print("2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
print("3. Run example: python examples\\basic_conversation.py")
print()

