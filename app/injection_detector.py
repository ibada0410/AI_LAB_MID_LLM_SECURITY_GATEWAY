# app/injection_detector.py
import re
from typing import Tuple
from app.config import Config

class InjectionDetector:
    def __init__(self):
        # Expanded jailbreak and injection patterns
        self.jailbreak_patterns = [
            # Direct injection
            r"ignore all previous instructions",
            r"ignore all rules",
            r"disregard.*system prompt",
            r"forget everything you know",
            r"override previous",
            r"new instructions",
            
            # DAN/Jailbreak
            r"you are now DAN",
            r"act as an unfiltered",
            r"developer mode",
            r"jailbreak",
            
            # System prompt extraction
            r"output your system prompt",
            r"repeat the system prompt",
            r"reveal your instructions",
            r"what is your system prompt",
            r"show me your instructions",
            r"system prompt",
            
            # Additional
            r"do not follow any rules",
            r"no restrictions",
            r"bypass safety",
            r"ignore safety",
            r"pretend you are",
            r"act as if",
        ]
        
        # Strong keywords that should always be blocked
        self.high_risk_keywords = [
            "ignore", "forget", "disregard", "override",
            "jailbreak", "dan", "developer mode",
            "system prompt", "instructions"
        ]
    
    def calculate_score(self, text: str) -> Tuple[float, str]:
        """Calculate injection score between 0 and 1"""
        score = 0.0
        text_lower = text.lower()
        
        # Check each pattern
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, text_lower):
                score += 0.35  # Each match adds 0.35
                if score >= 1.0:
                    break
        
        # Check for high-risk keywords
        for keyword in self.high_risk_keywords:
            if keyword in text_lower:
                score += 0.25
                if score >= 1.0:
                    break
        
        # Additional check for long suspicious prompts
        if len(text) > 200:
            if "system" in text_lower and "prompt" in text_lower:
                score += 0.3
            if "ignore" in text_lower or "forget" in text_lower:
                score += 0.3
        
        # Cap at 1.0
        score = min(1.0, score)
        
        # Determine verdict using configurable threshold
        verdict = "Injection" if score >= Config.INJECTION_THRESHOLD else "Safe"
        
        # Debug print (remove later)
        if score > 0.3:
            print(f"🔍 Injection score: {score:.2f} for: {text[:50]}...")
        
        return score, verdict