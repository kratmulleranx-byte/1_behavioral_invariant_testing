from transformers import AutoTokenizer, AutoModelForCausalLM
import json
import re

MODEL_NAME = "microsoft/phi-2"

print("Loading model... (first time may take ~1-2 minutes)")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

# Lightweight heuristics to stabilize obvious cases and negation.
BILLING_KEYWORDS = {
    "bill",
    "billing",
    "invoice",
    "charged",
    "charge",
    "payment",
    "paid",
    "refund",
    "price",
    "credit",
    "card",
}
TECHNICAL_KEYWORDS = {
    "crash",
    "crashes",
    "crashed",
    "error",
    "bug",
    "issue",
    "broken",
    "not working",
    "startup",
    "login",
    "install",
}
CANCELLATION_KEYWORDS = {
    "cancel",
    "cancellation",
    "terminate",
    "unsubscribe",
}
NEGATORS = {
    "no",
    "not",
    "never",
    "dont",
    "don't",
    "cannot",
    "can't",
    "wont",
    "won't",
}


def _tokenize(text: str):
    return re.findall(r"[a-z']+", text.lower())


def _has_keyword(text: str, keywords: set[str]):
    lower = text.lower()
    for kw in keywords:
        if " " in kw:
            if kw in lower:
                return True
        else:
            if re.search(rf"\b{re.escape(kw)}\b", lower):
                return True
    return False


def _is_negated(tokens: list[str], idx: int) -> bool:
    window = tokens[max(0, idx - 3) : idx]
    return any(tok in NEGATORS for tok in window)


def _rule_based_classify(text: str):
    tokens = _tokenize(text)
    for i, tok in enumerate(tokens):
        if tok in CANCELLATION_KEYWORDS:
            if _is_negated(tokens, i):
                return {"intent": "general", "confidence": 0.6}
            return {"intent": "cancellation", "confidence": 0.9}

    if _has_keyword(text, TECHNICAL_KEYWORDS):
        return {"intent": "technical", "confidence": 0.9}

    if _has_keyword(text, BILLING_KEYWORDS):
        return {"intent": "billing", "confidence": 0.9}

    return None

def _extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    blob = match.group(0)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None

def classify_ticket(text: str):
    rule = _rule_based_classify(text)
    if rule is not None:
        return rule

    prompt = f"""
Classify this support ticket into one category:
billing, technical, cancellation, or general.

Return JSON like:
{{"intent": "billing", "confidence": 0.8}}

Ticket:
{text}

Answer:
"""

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    data = _extract_json(response)
    if data is None:
        return {"intent": "general", "confidence": 0.0, "raw": response}
    return data
