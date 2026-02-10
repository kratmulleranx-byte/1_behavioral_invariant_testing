from model import classify_ticket

tests = [
    "I was charged twice this month.",
    "My app crashes when I try to log in.",
    "Please cancel my subscription.",
    "Do you have student discounts?"
]

for t in tests:
    print(t)
    print(classify_ticket(t))
    print("-" * 40)
