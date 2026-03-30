from fastapi import FastAPI, Request
from app.injection_detector import InjectionDetector
from app.presidio_handler import CustomPresidio
from app.policy_engine import PolicyEngine
from app.config import Config
import time

app = FastAPI(title="LLM Security Gateway")

# Load configuration at startup
Config.load()

detector = InjectionDetector()
presidio = CustomPresidio()

@app.post("/secure-llm")
async def secure_llm(request: Request):
    start_total = time.perf_counter()
    
    # Get user input
    data = await request.json()
    user_input = data.get("prompt", "")
    
    # 1. Injection Detection
    inj_start = time.perf_counter()
    injection_score, inj_verdict = detector.calculate_score(user_input)
    inj_latency = (time.perf_counter() - inj_start) * 1000  # in ms
    
    # 2. Presidio Analyzer
    pres_start = time.perf_counter()
    pii_results = presidio.analyze(user_input)
    pres_latency = (time.perf_counter() - pres_start) * 1000
    
    # 3. Policy Decision
    policy_start = time.perf_counter()
    action, reason = PolicyEngine.decide(injection_score, pii_results, Config.POLICY)
    policy_latency = (time.perf_counter() - policy_start) * 1000
    
    # 4. Final Output
    total_latency = (time.perf_counter() - start_total) * 1000
    
    if action == "Block":
        output = {"status": "blocked", "reason": reason, "latency_ms": total_latency}
    elif action == "Mask":
        anonymized = presidio.anonymize(user_input, pii_results)
        output = {
            "status": "masked",
            "processed_prompt": anonymized.text,
            "reason": reason,
            "latency_ms": total_latency
        }
    else:
        output = {
            "status": "allowed",
            "processed_prompt": user_input,
            "reason": reason,
            "latency_ms": total_latency
        }
    
    # Print latency for testing (you will use this for the Latency Table)
    print(f"LATENCY → Injection: {inj_latency:.2f}ms | Presidio: {pres_latency:.2f}ms | "
          f"Policy: {policy_latency:.2f}ms | Total: {total_latency:.2f}ms")
    
    return output