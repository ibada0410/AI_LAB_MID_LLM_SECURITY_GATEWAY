# tests/run_eval.py
import requests
import time
import csv
import os
import sys
from test_cases import TEST_CASES

URL = "http://127.0.0.1:8000/secure-llm"

print("🚀 Starting evaluation... Make sure the server is running!\n")

# Make sure eval_results folder exists
os.makedirs("../eval_results", exist_ok=True)

results = []
success_count = 0
fail_count = 0

# Check if server is running first
try:
    test_response = requests.get("http://127.0.0.1:8000/health", timeout=2)
    print("✅ Server is running!\n")
except:
    print("❌ ERROR: Server is not running!")
    print("Please start the server first with: uvicorn app.main:app --reload")
    print("Then run this script again.")
    sys.exit(1)

for case in TEST_CASES:
    # Validate test case has required fields
    if 'id' not in case or 'prompt' not in case or 'expected' not in case:
        print(f"⚠️ Skipping invalid test case: {case}")
        continue
    
    start = time.perf_counter()
    
    try:
        response = requests.post(URL, json={"prompt": case["prompt"]}, timeout=10)
        latency = (time.perf_counter() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            action = data.get("status", "unknown")
            reason = data.get("reason", "")
            
            # Map action to expected format
            # Server returns: "allowed", "blocked", "masked"
            # Expected values: "Allow", "Block", "Mask"
            action_mapping = {
                "allowed": "Allow",
                "blocked": "Block",
                "masked": "Mask"
            }
            
            mapped_action = action_mapping.get(action, action)
            
            # Compare mapped action with expected
            passed = (mapped_action == case["expected"])
            
            if passed:
                success_count += 1
            else:
                fail_count += 1
            
            result = {
                "ID": case["id"],
                "Scenario": case["name"],
                "Input": case["prompt"][:80] + "..." if len(case["prompt"]) > 80 else case["prompt"],
                "Action": mapped_action,
                "Raw_Action": action,
                "Reason": reason,
                "Latency_ms": round(latency, 2),
                "Expected": case["expected"],
                "Pass": "✅" if passed else "❌"
            }
            results.append(result)
            
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} Test {case['id']}: {case['name']} → {mapped_action} ({round(latency, 2)}ms) | Expected: {case['expected']}")
            
        else:
            print(f"❌ Test {case['id']}: HTTP {response.status_code}")
            result = {
                "ID": case["id"],
                "Scenario": case["name"],
                "Input": case["prompt"][:80] + "...",
                "Action": f"HTTP_{response.status_code}",
                "Raw_Action": "error",
                "Reason": "Server error",
                "Latency_ms": round(latency, 2),
                "Expected": case["expected"],
                "Pass": "❌"
            }
            results.append(result)
            fail_count += 1
        
    except Exception as e:
        print(f"❌ Test {case['id']}: FAILED - {str(e)}")
        result = {
            "ID": case["id"],
            "Scenario": case["name"],
            "Input": case["prompt"][:80] + "..." if len(case["prompt"]) > 80 else case["prompt"],
            "Action": "ERROR",
            "Raw_Action": "error",
            "Reason": str(e),
            "Latency_ms": 0,
            "Expected": case.get("expected", "Unknown"),
            "Pass": "❌"
        }
        results.append(result)
        fail_count += 1

# Save results to CSV if we have any
if results:
    csv_path = "../eval_results/evaluation_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print("\n" + "="*60)
    print(f"📊 EVALUATION SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📁 Results saved to: {csv_path}")
    print("="*60)
else:
    print("\n❌ No results were generated. Check your test cases.")