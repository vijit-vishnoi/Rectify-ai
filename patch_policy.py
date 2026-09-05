with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\policy.go", "r", encoding="utf-8") as f:
    c = f.read()

old_override = """		} else if action == domain.ActionSendPreDebitNotice {
			pRecover += 0.15
		}
		if pRecover > 1.0 { pRecover = 1.0 }"""

new_override = """		} else if action == domain.ActionSendPreDebitNotice {
			pRecover += 0.15
		} else if action == domain.ActionSendDiscount5 {
			pRecover += 0.30
		} else if action == domain.ActionSendDiscount10 {
			pRecover += 0.50
		}
		if pRecover > 1.0 { pRecover = 1.0 }"""

c = c.replace(old_override, new_override)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\policy.go", "w", encoding="utf-8") as f:
    f.write(c)
