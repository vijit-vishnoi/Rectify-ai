with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

# Fix: order.paid and subscription.charged are string comparisons but Event is now EventType
# Need to cast or compare properly
c = c.replace('if payload.Event == "order.paid" || payload.Event == "subscription.charged"',
              'if payload.Event == EventType("order.paid") || payload.Event == EventType("subscription.charged")')

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
