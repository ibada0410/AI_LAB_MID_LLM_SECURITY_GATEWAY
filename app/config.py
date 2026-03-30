# app/config.py
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Default values
    INJECTION_THRESHOLD = 0.65
    PII_CONFIDENCE_THRESHOLD = 0.60
    POLICY = "MASK"
    ALLOWED_POLICIES = ["Allow", "Mask", "Block"]
    CUSTOM_ENTITIES = ["PHONE_NUMBER", "API_KEY", "INTERNAL_ID", "COMPOSITE_CONTACT"]
    
    @classmethod
    def load(cls):
        """Load configuration from config.yaml if it exists"""
        try:
            with open("config.yaml", "r") as f:
                data = yaml.safe_load(f)
                for key, value in data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
            print(f"✅ Config loaded from config.yaml")
        except FileNotFoundError:
            print(f"⚠️ config.yaml not found, using defaults")
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using defaults")
        
        print(f"📋 Current config: INJECTION_THRESHOLD={cls.INJECTION_THRESHOLD}, POLICY={cls.POLICY}")

# Test configuration on import
if __name__ == "__main__":
    Config.load()