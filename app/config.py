import yaml
from dotenv import load_dotenv
load_dotenv()

class Config:
    INJECTION_THRESHOLD = 0.65          # configurable
    PII_CONFIDENCE_THRESHOLD = 0.60
    POLICY = "MASK"                     # default: Allow, Mask, Block
    ALLOWED_POLICIES = ["Allow", "Mask", "Block"]
    
    # Custom entities
    CUSTOM_ENTITIES = ["PHONE_NUMBER", "API_KEY", "INTERNAL_ID", "COMPOSITE_CONTACT"]
    
    @classmethod
    def load(cls):
        with open("config.yaml") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            setattr(cls, k, v)