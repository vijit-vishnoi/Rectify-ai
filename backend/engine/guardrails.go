package engine

import (
	"log"
	"rectify-ai-backend/domain"
	"time"
)

type Rule interface {
	Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string)
}

type TerminalFailureRule struct{}

func (r TerminalFailureRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop {
		return true, ""
	}
	terminalCodes := map[string]bool{
		"mandate_revoked": true,
		"suspected_fraud": true,
		"account_closed":  true,
	}
	if terminalCodes[evt.ErrorCode] {
		return false, "terminal_failure_class"
	}
	return true, ""
}

type MaxRetriesRule struct{}

func (r MaxRetriesRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop || action == domain.ActionWait {
		return true, ""
	}
	
	attempts := state.GetHistoricalAttemptCount(evt.ID)
	
	GlobalConfig.mu.RLock()
	maxAttempts := GlobalConfig.Data.Guardrails.MaxRetries
	GlobalConfig.mu.RUnlock()

	if attempts >= maxAttempts {
		log.Printf("[ENGINE] MaxRetriesRule: Vetoed %s. Total Historical Attempts (%d) >= Max (%d)", action, attempts, maxAttempts)
		return false, "max_attempts_reached"
	}
	return true, ""
}

type TRAIQuietHoursRule struct{}

func (r TRAIQuietHoursRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	// Temporary bypass for demo
	return true, ""
}

type OutOfBandSettlementRule struct{}

func (r OutOfBandSettlementRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop {
		return true, ""
	}
	if state.IsSettled(evt.ID) {
		log.Printf("[ENGINE] Aborted recovery: %s was settled out-of-band.", evt.ID)
		return false, "already_settled"
	}
	return true, ""
}

type RBIPreDebitNoticeRule struct{}

func (r RBIPreDebitNoticeRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionRetrySame || action == domain.ActionRetryAlt {
		if evt.FastForward24h {
			return true, ""
		}
		if !state.HasValidPreDebitNotice(evt.ID) {
			log.Printf("[ENGINE] RBI Rule: Vetoed %s. Missing or pending pre-debit notice for %s", action, evt.ID)
			return false, "missing_rbi_pre_debit_notice"
		}
	}
	return true, ""
}





type NoticeCooldownRule struct{}

func (r NoticeCooldownRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionSendPreDebitNotice {
		if state.GetHistoricalAttemptCount(evt.ID) >= 1 {
			return false, "pre_debit_notice_cooldown"
		}
	}
	return true, ""
}

type HinglishVoiceRule struct{}

func (r HinglishVoiceRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action != domain.ActionEscalateVoiceHinglish {
		return true, ""
	}
	if evt.Amount < 100000 {
		return false, "insufficient_amount_for_voice"
	}
	if state.GetHistoricalAttemptCount(evt.ID) < 2 {
		return false, "insufficient_attempts_for_voice"
	}
	return true, ""
}

type PromiseToPayRule struct{}

func (r PromiseToPayRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop {
		return true, ""
	}
	if state.HasActivePromiseToPay(evt.ID) {
		if action != domain.ActionPromisePending {
			log.Printf("[ENGINE] PromiseToPayRule: Vetoed intrusive action %s. Active hold for %s", action, evt.ID)
			return false, "active_promise_to_pay"
		}
	} else {
		if action == domain.ActionPromisePending {
			return false, "no_active_promise"
		}
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
	if action == domain.ActionStop || action == domain.ActionSendPreDebitNotice || action == domain.ActionNudge || action == domain.ActionWait || action == domain.ActionSendDiscount5 || action == domain.ActionSendDiscount10 || action == domain.ActionPromisePending {
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


type MaxDiscountRule struct{}

func (r MaxDiscountRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action != domain.ActionSendDiscount5 && action != domain.ActionSendDiscount10 {
		return true, ""
	}
	
	marginThreshold := int64(100000) // 1000.00 INR
	if evt.Amount < marginThreshold {
		log.Printf("[ENGINE] MaxDiscountRule: Vetoed %s. Cart Value (%d) < Margin Threshold (%d)", action, evt.Amount, marginThreshold)
		return false, "cart_value_below_discount_margin"
	}
	return true, ""
}

func CheckGuardrails(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	rules := []Rule{
		TerminalFailureRule{},
		ColdStartRule{},
		MaxRetriesRule{},
		TRAIQuietHoursRule{},
		OutOfBandSettlementRule{},
		RBIPreDebitNoticeRule{},
		NoticeCooldownRule{},
		PromiseToPayRule{},
		MaxAgeRule{},
		MaxDiscountRule{},
		HinglishVoiceRule{},
	}

	for _, rule := range rules {
		if allowed, reason := rule.Check(state, evt, action); !allowed {
			return false, reason
		}
	}
	return true, ""
}



