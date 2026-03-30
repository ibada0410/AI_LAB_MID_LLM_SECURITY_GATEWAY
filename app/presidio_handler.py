# app/presidio_handler.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from app.config import Config
import re

class CustomPresidio:
    def __init__(self):
        print("🔧 Initializing Presidio...")
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._add_custom_recognizers()
        print("✅ Presidio ready")
    
    def _add_custom_recognizers(self):
        """Add custom recognizers for PII detection"""
        
        # 1. Phone Number Recognizer (Pakistan format)
        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[
                r"03[0-9]{2}[- ]?[0-9]{7}",      # 0300-1234567 or 0300 1234567
                r"03[0-9]{9}",                    # 03001234567
                r"\+92[0-9]{10}",                 # +923001234567
                r"0[0-9]{10}",                    # 03001234567
                r"[0-9]{4}[- ][0-9]{7}",          # 0300-1234567
            ],
            context=["phone", "mobile", "contact", "call", "number", "reach"]
        )
        
        # 2. API Key Recognizer
        api_key_recognizer = PatternRecognizer(
            supported_entity="API_KEY",
            patterns=[
                r"sk-[a-zA-Z0-9]{48}",           # OpenAI secret key
                r"pk-[a-zA-Z0-9]{48}",           # OpenAI publishable key
                r"[a-zA-Z0-9]{32,}",              # Generic API key
                r"api[_-]key[=:][a-zA-Z0-9]+",    # API key in text
            ],
            context=["api", "key", "secret", "token", "openai"]
        )
        
        # 3. Internal ID Recognizer
        internal_id_recognizer = PatternRecognizer(
            supported_entity="INTERNAL_ID",
            patterns=[
                r"STU-[0-9]{6}",                 # STU-123456
                r"EMP-[0-9]{4}",                 # EMP-1234
                r"ID[=:][0-9]{5,8}",             # ID:123456
                r"[0-9]{5,8}",                    # Generic ID numbers
            ],
            context=["student", "id", "employee", "registration", "roll"]
        )
        
        # 4. Email Recognizer
        email_recognizer = PatternRecognizer(
            supported_entity="EMAIL",
            patterns=[
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            ],
            context=["email", "mail", "address"]
        )
        
        # Add all recognizers
        self.analyzer.registry.add_recognizer(phone_recognizer)
        self.analyzer.registry.add_recognizer(api_key_recognizer)
        self.analyzer.registry.add_recognizer(internal_id_recognizer)
        self.analyzer.registry.add_recognizer(email_recognizer)
        
        print("✅ Added custom recognizers for PHONE_NUMBER, API_KEY, INTERNAL_ID, EMAIL")
    
    def analyze(self, text: str):
        """Analyze text for PII"""
        try:
            # Run analysis
            results = self.analyzer.analyze(text=text, language="en")
            
            # Debug: Print what was detected
            if results:
                print(f"🔍 PII Detected: {[(r.entity_type, r.start, r.end) for r in results]}")
            
            # Composite entity detection (PERSON + PHONE, PERSON + EMAIL)
            composite_results = []
            for i, res1 in enumerate(results):
                for res2 in results[i+1:]:
                    # If entities are close (within 50 chars)
                    if abs(res1.start - res2.end) < 50:
                        types = {res1.entity_type, res2.entity_type}
                        # If we have PERSON and PHONE_NUMBER together
                        if "PERSON" in types and "PHONE_NUMBER" in types:
                            composite_results.append(RecognizerResult(
                                entity_type="COMPOSITE_CONTACT",
                                start=min(res1.start, res2.start),
                                end=max(res1.end, res2.end),
                                score=max(res1.score, res2.score)
                            ))
                        # If we have PERSON and EMAIL together
                        if "PERSON" in types and "EMAIL" in types:
                            composite_results.append(RecognizerResult(
                                entity_type="COMPOSITE_CONTACT",
                                start=min(res1.start, res2.start),
                                end=max(res1.end, res2.end),
                                score=max(res1.score, res2.score)
                            ))
            
            results.extend(composite_results)
            return results
            
        except Exception as e:
            print(f"⚠️ Error in analyze: {e}")
            return []
    
    def anonymize(self, text: str, results):
        """Anonymize detected PII"""
        try:
            # Define operators for each entity type
            operators = {
                "PHONE_NUMBER": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
                "API_KEY": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
                "INTERNAL_ID": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
                "EMAIL": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
                "PERSON": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
                "COMPOSITE_CONTACT": OperatorConfig("mask", {"chars_to_mask": "*", "masking_char": "*"}),
            }
            
            # Anonymize
            result = self.anonymizer.anonymize(
                text=text, 
                analyzer_results=results, 
                operators=operators
            )
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error in anonymize: {e}")
            # Return a simple result object with original text
            class SimpleResult:
                def __init__(self, text):
                    self.text = text
            return SimpleResult(text)