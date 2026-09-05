with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('if payload.Event == EventType("order.paid") || payload.Event == EventType("subscription.charged")',
              'if payload.Event == domain.EventType("order.paid") || payload.Event == domain.EventType("subscription.charged")')

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
