with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go", "r", encoding="utf-8") as f:
    c = f.read()

old = """	rules := []Rule{
		TerminalFailureRule{},
		ColdStartRule{},
		MaxRetriesRule{},
		TRAIQuietHoursRule{},
		OutOfBandSettlementRule{},
		RBIPreDebitNoticeRule{},
		PromiseToPayRule{},
		MaxAgeRule{},
	}"""
new = """	rules := []Rule{
		TerminalFailureRule{},
		ColdStartRule{},
		MaxRetriesRule{},
		TRAIQuietHoursRule{},
		OutOfBandSettlementRule{},
		RBIPreDebitNoticeRule{},
		PromiseToPayRule{},
		MaxAgeRule{},
		MaxDiscountRule{},
	}"""
c = c.replace(old, new)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go", "w", encoding="utf-8") as f:
    f.write(c)
