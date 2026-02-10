from model import classify_ticket

def test_billing_keywords_never_technical():
    samples = [
        "I was charged twice",
        "Refund my last invoice",
        "My payment failed",
    ]

    for text in samples:
        result = classify_ticket(text)
        assert result["intent"] != "technical", result
