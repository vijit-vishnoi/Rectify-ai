import re

with open(r'd:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go', 'r') as f:
    c = f.read()

missing_rules = '''
type PromiseToPayRule struct{}

func (r PromiseToPayRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop {
		return true, ""
	}
	if state.HasActivePromiseToPay(evt.ID) {
		log.Printf("[ENGINE] PromiseToPayRule: Vetoed intrusive action %s. Active hold for %s", action, evt.ID)
		return false, "active_promise_to_pay"
	}
	return true, ""
}

type MaxAgeRule struct{}

func (r MaxAgeRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop {
		return true, ""
	}
	
	GlobalConfig.mu.RLock()
	maxAgeDays := GlobalConfig.Data.Guardrails.MaxAgeDays
	GlobalConfig.mu.RUnlock()

	if time.Since(evt.OccurredAt) > time.Duration(maxAgeDays)*24*time.Hour {
		log.Printf("[ENGINE] MaxAgeRule: Vetoed action %s. Receivable %s is older than %d days.", action, evt.ID, maxAgeDays)
		return false, "exceeds_max_age"
	}
	return true, ""
}

type ColdStartRule struct{}

func (r ColdStartRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop || action == domain.ActionSendPreDebitNotice || action == domain.ActionNudge || action == domain.ActionWait {
		return true, ""
	}
	
	if state.GetHistoricalAttemptCount(evt.ID) < 1 {
		if action == domain.ActionRetrySame {
			log.Printf("[COLD-START] Bypassing AI scoring for uncalibrated receivable: %s. Enforcing onboarding rulebook.", evt.ID)
		}
		return false, "cold_start_onboarding"
	}
	return true, ""
}

func CheckGuardrails(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {'''

c = c.replace('func CheckGuardrails(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {', missing_rules)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go', 'w') as f:
    f.write(c)
