from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngine, SpacyNlpEngine
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from app.config import Config

class CustomPresidio:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._add_custom_recognizers()
        self.context_enhancer = LemmaContextAwareEnhancer(
            context_similarity_factor=0.45,
            min_score_with_context_similarity=0.4
        )
    
    def _add_custom_recognizers(self):
        # 1. Custom recognizer (PHONE + API_KEY + INTERNAL_ID)
        api_key_recognizer = PatternRecognizer(
            supported_entity="API_KEY",
            patterns=[r"sk-[a-zA-Z0-9]{48}", r"pk-[a-zA-Z0-9]{48}"],
            context=["api", "key", "secret", "token"]
        )
        internal_id_recognizer = PatternRecognizer(
            supported_entity="INTERNAL_ID",
            patterns=[r"STU-[0-9]{6}", r"EMP-[0-9]{4}"],  # your uni format
            context=["student", "id", "employee"]
        )
        self.analyzer.registry.add_recognizer(api_key_recognizer)
        self.analyzer.registry.add_recognizer(internal_id_recognizer)
    
    def analyze(self, text: str):
        # 2. Context-aware scoring (already enhanced)
        results = self.analyzer.analyze(text=text, language="en")
        
        # 3. Composite entity detection (post-processing)
        composite_results = []
        for i, res1 in enumerate(results):
            for res2 in results[i+1:]:
                if abs(res1.start - res2.end) < 50 and {"PERSON", "PHONE_NUMBER"}.issubset({res1.entity_type, res2.entity_type}):
                    composite_results.append(RecognizerResult(
                        entity_type="COMPOSITE_CONTACT",
                        start=min(res1.start, res2.start),
                        end=max(res1.end, res2.end),
                        score=max(res1.score, res2.score)
                    ))
        results.extend(composite_results)
        
        return results
    
    def anonymize(self, text: str, results):
        operators = {entity: OperatorConfig("mask", {"chars_to_mask": "*"}) for entity in Config.CUSTOM_ENTITIES}
        return self.anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)