import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing with API key: {api_key[:20]}...")
print()

genai.configure(api_key=api_key)

print("Testing Gemma model...")
try:
    model = genai.GenerativeModel('models/gemma-3-4b-it')
    print("✅ Model initialized")
    
    print("Sending test message...")
    response = model.generate_content("Say 'hi' in a casual way")
    
    print("✅ Response received!")
    print(f"Luna: {response.text}")
    print()
    print("🎉 GEMMA API WORKS!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

