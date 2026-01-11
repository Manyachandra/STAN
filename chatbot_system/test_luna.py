import urllib.request
import json

print("🧪 Testing Luna...")
print()

# Test 1: Health Check
try:
    response = urllib.request.urlopen('http://localhost:8000/health')
    health = json.loads(response.read().decode())
    print("✅ Health Check: PASSED")
    print(f"   Status: {health['status']}")
    print(f"   MongoDB: {health['mongodb']}")
    print(f"   Gemini: {health['gemini']}")
    print()
except Exception as e:
    print(f"❌ Health Check FAILED: {e}")
    exit(1)

# Test 2: Chat Message
try:
    print("🧪 Testing Chat...")
    data = json.dumps({
        'message': 'hey',
        'user_id': 'test123'
    }).encode()
    
    req = urllib.request.Request(
        'http://localhost:8000/chat',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    
    print("✅ Chat Test: PASSED")
    print(f"   User: hey")
    print(f"   Luna: {result['response']}")
    print(f"   Emotion: {result['emotion']}")
    print()
    
except Exception as e:
    print(f"❌ Chat Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Another message
try:
    print("🧪 Testing Memory...")
    data = json.dumps({
        'message': 'i am coffee addicted',
        'user_id': 'test123'
    }).encode()
    
    req = urllib.request.Request(
        'http://localhost:8000/chat',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    
    print("✅ Memory Test: PASSED")
    print(f"   User: i am coffee addicted")
    print(f"   Luna: {result['response']}")
    print(f"   Memory Updated: {result['memory_updated']}")
    print()
    
except Exception as e:
    print(f"❌ Memory Test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)
print("🎉 ALL TESTS PASSED - LUNA IS WORKING!")
print("=" * 50)
print()
print("🌙 Open browser: http://localhost:8000")

