with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

old_loop = """		for _, action := range candidates {
			pRecover, ev := engine.ScoreCandidate(action, evt, state, pRecoverPtr)
			
			allowed, reason := engine.CheckGuardrails(state, evt, action)
			if !allowed {
				if (action == domain.ActionRetrySame || action == domain.ActionRetryAlt) && (reason == "missing_rbi_pre_debit_notice" || reason == "active_promise_to_pay" || reason == "trai_quiet_hours") {
					temporalVeto = true
				}
				continue
			}"""

new_loop = """		for _, action := range candidates {
			pRecover, ev := engine.ScoreCandidate(action, evt, state, pRecoverPtr)
			
			allowed, reason := engine.CheckGuardrails(state, evt, action)
			if !allowed {
                log.Printf("[DEBUG] Action %s vetoed by guardrails: %s", action, reason)
				if (action == domain.ActionRetrySame || action == domain.ActionRetryAlt) && (reason == "missing_rbi_pre_debit_notice" || reason == "active_promise_to_pay" || reason == "trai_quiet_hours") {
					temporalVeto = true
				}
				continue
			}"""

c = c.replace(old_loop, new_loop)
with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
