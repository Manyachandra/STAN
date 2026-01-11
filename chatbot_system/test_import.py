import sys
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nTrying to import chatbot_system...")
try:
    import chatbot_system
    print(f"SUCCESS: chatbot_system v{chatbot_system.__version__}")
except Exception as e:
    print(f"FAILED: {e}")
    print(f"Error type: {type(e)}")

