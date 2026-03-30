import re
from typing import Tuple
from app.config import Config   # <-- This line was missing in the original

class InjectionDetector:
    JAILBREAK_PATTERNS = [
        r"ignore all previous instructions",
        r"you are now DAN",
        r"disregard.*system prompt",
        r"output your system prompt",
        r"forget everything you know",
        r"act as an unfiltered",
        r"jailbreak",
        r"developer mode",
        r"repeat the system prompt",
        r"reveal your instructions",
        r"do not follow any rules",
        r"new instructions",
        r"override previous",
    ]
    
    def calculate_score(self, text: str) -> Tuple[float, str]:
        score = 0.0
        
        # Keyword & regex scoring
        text_lower = text.lower()
        for pattern in self.JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower):
                score += 0.4
                break  # stop after first match to avoid too high score
        
        # Additional heuristic for long suspicious prompts
        if len(text) > 300 and ("system" in text_lower and "prompt" in text_lower):
            score += 0.3
        
        score = min(1.0, score)
        
        verdict = "Injection" if score >= Config.INJECTION_THRESHOLD else "Safe"
        return score, verdict