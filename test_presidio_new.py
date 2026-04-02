# test_presidio_new.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

# Create analyzer
analyzer = AnalyzerEngine()

# Create pattern using Pattern class
patterns = [Pattern(name="phone", regex=r"03[0-9]{2}[- ]?[0-9]{7}", score=0.85)]
phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=patterns
)
analyzer.registry.add_recognizer(phone_recognizer)

# Test
text = "My phone is 0300-1234567"
results = analyzer.analyze(text=text, language="en")

print(f"Text: {text}")
if results:
    for r in results:
        print(f"Found: {r.entity_type} - '{text[r.start:r.end]}'")
else:
    print("No PII detected")