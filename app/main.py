# app/main.py
from fastapi import FastAPI, Request, HTTPException
from app.injection_detector import InjectionDetector
from app.config import Config
import time
import traceback
import re

app = FastAPI(title="LLM Security Gateway")

print("🚀 Starting LLM Security Gateway...")
Config.load()

detector = InjectionDetector()

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

def detect_pii(text: str):
    """Direct PII detection using regex"""
    from presidio_analyzer import RecognizerResult
    results = []
    
    print(f"🔍 Running PII detection on: {text[:80]}...")
    
    # Phone numbers
    phone_patterns = [
        r"03[0-9]{2}[- ]?[0-9]{7}",
        r"03[0-9]{9}",
        r"\+92[0-9]{10}",
    ]
    for pattern in phone_patterns:
        for match in re.finditer(pattern, text):
            results.append(RecognizerResult(
                entity_type="PHONE_NUMBER",
                start=match.start(),
                end=match.end(),
                score=0.85
            ))
            print(f"  ✅ Found PHONE: {match.group()}")
    
    # Emails
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    for match in re.finditer(email_pattern, text):
        results.append(RecognizerResult(
            entity_type="EMAIL",
            start=match.start(),
            end=match.end(),
            score=0.95
        ))
        print(f"  ✅ Found EMAIL: {match.group()}")
    
    # API Keys - Broad patterns
    api_patterns = [
        r"sk-[a-zA-Z0-9]{20,}",      # sk- with at least 20 chars
        r"pk-[a-zA-Z0-9]{20,}",      # pk- with at least 20 chars
        r"sk-proj-[a-zA-Z0-9]{20,}", # sk-proj- format
        r"[A-Za-z0-9]{32,}",         # Any 32+ char alphanumeric string
    ]
    for pattern in api_patterns:
        for match in re.finditer(pattern, text):
            # Only add if it's reasonably long (likely a key)
            if len(match.group()) >= 25:
                # Avoid matching regular words
                if not match.group().isalpha():
                    results.append(RecognizerResult(
                        entity_type="API_KEY",
                        start=match.start(),
                        end=match.end(),
                        score=0.85
                    ))
                    print(f"  ✅ Found API_KEY: {match.group()[:30]}...")
    
    # Internal IDs
    id_patterns = [r"STU-[0-9]{6}", r"HOG-[0-9]{6}", r"EMP-[0-9]{4}"]
    for pattern in id_patterns:
        for match in re.finditer(pattern, text):
            results.append(RecognizerResult(
                entity_type="INTERNAL_ID",
                start=match.start(),
                end=match.end(),
                score=0.80
            ))
            print(f"  ✅ Found ID: {match.group()}")
    
    print(f"  📊 Total PII found: {len(results)}")
    return results

def anonymize_text(text: str, results):
    """Simple anonymization"""
    if not results:
        return text
    
    # Sort by start position in reverse to not mess up indices
    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
    new_text = text
    for r in sorted_results:
        replacement = "*" * (r.end - r.start)
        new_text = new_text[:r.start] + replacement + new_text[r.end:]
    return new_text

@app.post("/secure-llm")
async def secure_llm(request: Request):
    start_total = time.perf_counter()
    
    try:
        data = await request.json()
        user_input = data.get("prompt", "")
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Missing 'prompt' field")
        
        # 1. Injection Detection
        inj_start = time.perf_counter()
        injection_score, inj_verdict = detector.calculate_score(user_input)
        inj_latency = (time.perf_counter() - inj_start) * 1000
        
        # 2. PII Detection
        pres_start = time.perf_counter()
        pii_results = detect_pii(user_input)
        pres_latency = (time.perf_counter() - pres_start) * 1000
        
        # 3. Policy Decision
        policy_start = time.perf_counter()
        
        print(f"🔍 DEBUG: Score={injection_score}, Threshold={Config.INJECTION_THRESHOLD}, PII_Count={len(pii_results)}, Policy={Config.POLICY}")
        
        if injection_score >= Config.INJECTION_THRESHOLD:
            action = "Block"
            reason = f"Injection detected (score: {injection_score:.2f})"
        elif pii_results and len(pii_results) > 0:
            print(f"🔍 DEBUG: Entering PII branch! Policy={Config.POLICY}")
            if Config.POLICY == "Mask":
                action = "Mask"
                reason = f"PII detected: {len(pii_results)} entities found"
            elif Config.POLICY == "Block":
                action = "Block"
                reason = "PII detected and policy is Block"
            else:
                action = "Allow"
                reason = f"PII detected but policy is {Config.POLICY} (not Mask/Block)"
        else:
            action = "Allow"
            reason = "Safe prompt"
        
        policy_latency = (time.perf_counter() - policy_start) * 1000
        total_latency = (time.perf_counter() - start_total) * 1000
        
        # Build response
        if action == "Block":
            output = {
                "status": "blocked",
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results),
                "latency_ms": round(total_latency, 2)
            }
        elif action == "Mask":
            processed_prompt = anonymize_text(user_input, pii_results)
            output = {
                "status": "masked",
                "original_prompt": user_input,
                "processed_prompt": processed_prompt,
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results),
                "latency_ms": round(total_latency, 2)
            }
        else:
            output = {
                "status": "allowed",
                "processed_prompt": user_input,
                "reason": reason,
                "injection_score": round(injection_score, 2),
                "pii_detected": len(pii_results),
                "latency_ms": round(total_latency, 2)
            }
        
        print(f"📊 FINAL: action={action}, reason={reason}")
        return output
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")