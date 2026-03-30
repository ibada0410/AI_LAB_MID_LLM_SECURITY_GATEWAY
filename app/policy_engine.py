from app.config import Config

class PolicyEngine:
    @staticmethod
    def decide(injection_score: float, pii_results, policy: str):
        # If injection is detected → always Block
        if injection_score >= Config.INJECTION_THRESHOLD:
            return "Block", "Injection detected"
        
        # If PII is found and policy is Mask or Block
        if pii_results:  # pii_results list is not empty
            if policy == "Mask":
                return "Mask", "PII masked"
            if policy == "Block":
                return "Block", "PII blocked"
        
        # Everything is safe
        return "Allow", "Safe"