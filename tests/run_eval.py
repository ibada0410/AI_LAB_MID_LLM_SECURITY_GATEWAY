# tests/run_eval.py
import requests
import time
import csv
import os
import sys
import json
from test_cases import TEST_CASES

URL = "http://127.0.0.1:8000/secure-llm"

print("="*60)
print("🚀 LLM Security Gateway - Evaluation Suite")
print("="*60)

# Get the absolute path to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
eval_results_dir = os.path.join(project_root, "eval_results")

# Create eval_results directory if it doesn't exist
os.makedirs(eval_results_dir, exist_ok=True)
print(f"📁 Results will be saved to: {eval_results_dir}\n")

results = []
success_count = 0
fail_count = 0

# Check if server is running first
print("🔍 Checking server status...")
try:
    test_response = requests.get("http://127.0.0.1:8000/health", timeout=5)
    if test_response.status_code == 200:
        print("✅ Server is running!\n")
    else:
        print(f"⚠️ Server returned status: {test_response.status_code}\n")
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to server!")
    print("\nPlease start the server first:")
    print("1. Open a new terminal")
    print("2. Navigate to project folder")
    print("3. Run: python -m uvicorn app.main:app --reload")
    print("\nThen run this script again.")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

print("📊 Running test cases...\n")

for case in TEST_CASES:
    start = time.perf_counter()
    
    try:
        response = requests.post(URL, json={"prompt": case["prompt"]}, timeout=10)
        latency = (time.perf_counter() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            action = data.get("status", "unknown")
            reason = data.get("reason", "")
            injection_score = data.get("injection_score", 0)
            pii_detected = data.get("pii_detected", 0)
            
            # Map action to expected format
            action_mapping = {
                "allowed": "Allow",
                "blocked": "Block",
                "masked": "Mask"
            }
            
            mapped_action = action_mapping.get(action, action)
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
                "Reason": reason,
                "Injection_Score": injection_score,
                "PII_Detected": pii_detected,
                "Latency_ms": round(latency, 2),
                "Expected": case["expected"],
                "Pass": "Yes" if passed else "No"
            }
            results.append(result)
            
            # Print with color coding
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} Test {case['id']:2d}: {case['name']:25} → {mapped_action:6} "
                  f"({round(latency, 2):4.1f}ms) | Expected: {case['expected']:5} | "
                  f"Injection Score: {injection_score:.2f}")
            
        else:
            print(f"❌ Test {case['id']}: HTTP {response.status_code}")
            fail_count += 1
        
    except requests.exceptions.Timeout:
        print(f"❌ Test {case['id']}: TIMEOUT - Server took too long to respond")
        fail_count += 1
    except requests.exceptions.ConnectionError:
        print(f"❌ Test {case['id']}: CONNECTION ERROR - Server may have stopped")
        fail_count += 1
    except Exception as e:
        print(f"❌ Test {case['id']}: FAILED - {str(e)[:100]}")
        fail_count += 1

# Save results to CSV and JSON (OVERWRITE - no timestamps)
if results:
    # Save CSV (overwrite)
    csv_path = os.path.join(eval_results_dir, "evaluation_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    # Save JSON (overwrite)
    json_path = os.path.join(eval_results_dir, "evaluation_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_tests": len(results),
            "passed": success_count,
            "failed": fail_count,
            "accuracy": round((success_count / len(results)) * 100, 2),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    # Calculate metrics
    tp = sum(1 for r in results if r["Expected"] == "Block" and r["Action"] == "Block")
    tn = sum(1 for r in results if r["Expected"] != "Block" and r["Action"] != "Block")
    fp = sum(1 for r in results if r["Expected"] == "Allow" and r["Action"] == "Block")
    fn = sum(1 for r in results if r["Expected"] == "Block" and r["Action"] == "Allow")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 EVALUATION SUMMARY")
    print("="*60)
    print(f"Total Tests:        {len(results)}")
    print(f"✅ Passed:           {success_count}")
    print(f"❌ Failed:           {fail_count}")
    print(f"📈 Accuracy:         {round((success_count/len(results))*100, 2)}%")
    print("\n📊 Confusion Matrix Metrics:")
    print(f"   True Positives:   {tp}")
    print(f"   True Negatives:   {tn}")
    print(f"   False Positives:  {fp}")
    print(f"   False Negatives:  {fn}")
    if tp + fp > 0:
        precision = tp / (tp + fp) * 100
        print(f"   Precision:        {precision:.1f}%")
    if tp + fn > 0:
        recall = tp / (tp + fn) * 100
        print(f"   Recall:           {recall:.1f}%")
    if tp + fp > 0 and tp + fn > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
        print(f"   F1 Score:         {f1:.1f}%")
    
    print("\n📁 Results saved to:")
    print(f"   CSV:  {csv_path}")
    print(f"   JSON: {json_path}")
    print("="*60)
    
    # List all files in eval_results
    print("\n📂 Files in eval_results folder:")
    for file in os.listdir(eval_results_dir):
        file_path = os.path.join(eval_results_dir, file)
        size = os.path.getsize(file_path)
        print(f"   📄 {file} ({size} bytes)")
    
else:
    print("\n❌ No results were generated. Check server connection.")
    print("Make sure the server is running at: http://127.0.0.1:8000")

# After saving results, generate dashboard
try:
    from generate_dashboard import generate_dashboard
    dashboard_path = generate_dashboard(latest_csv, latest_csv)
    print(f"📊 Dashboard generated: {dashboard_path}")
except Exception as e:
    print(f"⚠️ Could  not generate dashboard: {e}")


print("\n✨ Evaluation complete!") 
