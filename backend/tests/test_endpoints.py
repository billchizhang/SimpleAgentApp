import urllib.request
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, path, expected_keys=None, expected_val=None):
    print(f"Testing {name}...", end=" ")
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}") as response:
            if response.status != 200:
                print(f"FAILED (Status {response.status})")
                return False
            data = json.loads(response.read().decode())
            
            if expected_keys:
                for key in expected_keys:
                    if key not in data:
                        print(f"FAILED (Missing key {key})")
                        return False
            
            if expected_val:
                for k, v in expected_val.items():
                    if data.get(k) != v:
                        print(f"FAILED (Expected {k}={v}, got {data.get(k)})")
                        return False
            
            print(f"PASSED. Response: {data}")
            return True
    except Exception as e:
        print(f"FAILED (Exception: {e})")
        return False

def run_tests():
    # Wait for server to start
    time.sleep(2)
    
    success = True
    
    # 1. get_weather
    if not test_endpoint("get_weather", "/weather?city=London&date=2023-10-27", ["date", "city", "temperature_c"], {"city": "London", "date": "2023-10-27"}):
        success = False

    # 2. get_uppercase
    if not test_endpoint("get_uppercase", "/uppercase?text=hello", ["text"], {"text": "HELLO"}):
        success = False

    # 3. get_lowercase
    if not test_endpoint("get_lowercase", "/lowercase?text=WORLD", ["text"], {"text": "world"}):
        success = False

    # 4. count_word
    if not test_endpoint("count_word", "/count_word?text=hello%20world", ["word_count"], {"word_count": 2}):
        success = False

    # 5. calculate
    # Test +
    if not test_endpoint("calculate", "/calculate?a=5&b=3&operation=%2B", ["result"], {"result": 8.0}):
        success = False
    
    # Test / (division)
    if not test_endpoint("calculate", "/calculate?a=10&b=2&operation=/", ["result"], {"result": 5.0}):
        success = False

    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
