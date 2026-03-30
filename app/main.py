# app/main.py
from fastapi import FastAPI, Request, HTTPException
from app.injection_detector import InjectionDetector
from app.presidio_handler import CustomPresidio
from app.config import Config
import time
import traceback

# Create FastAPI app
app = FastAPI(title="LLM Security Gateway")

# Load configuration
print("🚀 Starting LLM Security Gateway...")
Config.load()

# Initialize components
detector = InjectionDetector()
presidio = CustomPresidio()

@app.get("/")
async def root():
    return {
        "message": "LLM Security Gateway is running", 
        "status": "active",
        "config": {
            "injection_threshold": Config.INJECTION_THRESHOLD,
            "policy": Config.POLICY
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "config": {
            "threshold": Config.INJECTION_THRESHOLD, 
            "policy": Config.POLICY
        }
    }

@app.post("/secure-llm")
async def secure_llm(request: Request):
    start_total = time.perf_counter()
    
    try:
        # Get user input
        data = await request.json()
        user_input = data.get("prompt", "")
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Missing 'prompt' field")
        
        # 1. Injection Detection
        inj_start = time.perf_counter()
        injection_score, inj_verdict = detector.calculate_score(user_input)
        inj_latency = (time.perf_counter() - inj_start) * 1000
        
        # 2. Presidio Analyzer (PII Detection)
        pres_start = time.perf_counter()
        pii_results = presidio.analyze(user_input)
        pres_latency = (time.perf_counter() - pres_start) * 1000
        
        # 3. Policy Decision
        policy_start = time.perf_counter()
        
        # Check injection first - if injection detected, always block
        if injection_score >= Config.INJECTION_THRESHOLD:
            action = "Block"
            reason = f"Injection detected (score: {injection_score:.2f})"
        
        # Check PII if no injection
        elif pii_results and len(pii_results) > 0:
            # Get policy from config (Allow, Mask, or Block)
            if Config.POLICY == "Mask":
                action = "Mask"
                reason = f"PII detected: {len(pii_results)} entities found"
            elif Config.POLICY == "Block":
                action = "Block"
                reason = f"PII detected and policy is Block"
            else:  # Allow
                action = "Allow"
                reason = "PII detected but policy is Allow (not blocking/masking)"
        
        # No injection, no PII - safe prompt
        else:
            action = "Allow"
            reason = "Safe prompt"
        
        policy_latency = (time.perf_counter() - policy_start) * 1000
        
        # 4. Prepare Final Output
        total_latency = (time.perf_counter() - start_total) * 1000
        
        # Build response based on action
        if action == "Block":
            output = {
                "status": "blocked",
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results) if pii_results else 0,
                "latency_ms": round(total_latency, 2),
                "original_prompt": user_input
            }
            
        elif action == "Mask":
            # Anonymize the PII
            anonymized_result = presidio.anonymize(user_input, pii_results)
            output = {
                "status": "masked",
                "original_prompt": user_input,
                "processed_prompt": anonymized_result.text,
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results),
                "pii_entities": [r.entity_type for r in pii_results],
                "latency_ms": round(total_latency, 2)
            }
            
        else:  # Allow
            output = {
                "status": "allowed",
                "processed_prompt": user_input,
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results) if pii_results else 0,
                "latency_ms": round(total_latency, 2)
            }
        
        # Print latency for debugging (useful for your Latency Table)
        print(f"📊 Latency - Total: {total_latency:.2f}ms | Injection: {inj_latency:.2f}ms | Presidio: {pres_latency:.2f}ms | Policy: {policy_latency:.2f}ms")
        print(f"📋 Decision: {action} | Score: {injection_score:.2f} | PII: {len(pii_results) if pii_results else 0}")
        
        return output
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")