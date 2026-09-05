package engine

import (
	"math"
	"rectify-ai-backend/domain"
)

func GenerateCandidates(evt domain.Event) []domain.Action {
	if evt.Type == domain.EventTypeCheckoutAbandoned {
		return []domain.Action{
			domain.ActionSendDiscount5,
			domain.ActionSendDiscount10,
			domain.ActionNudge,
		}
	}
	return []domain.Action{
		domain.ActionRetrySame,
		domain.ActionRetryAlt,
		domain.ActionNudge,
		domain.ActionSendPreDebitNotice,
		domain.ActionEscalateVoiceHinglish,
	domain.ActionPromisePending,
	}
}

func sigmoid(z float64) float64 {
	return 1.0 / (1.0 + math.Exp(-z))
}

func ScoreCandidate(action domain.Action, evt domain.Event, state *domain.MemoryState, basePRecover *float64) (float64, int64) {
	if action == domain.ActionStop || action == domain.ActionPromisePending {
		return 0.0, 0
	}
	if action == domain.ActionStop {
		return 0.0, 0
	}

	dayOfMonth := evt.OccurredAt.Day()
	isSalaryWindow := 0.0
	if dayOfMonth >= 1 && dayOfMonth <= 7 {
		isSalaryWindow = 1.0
	}

	highValueAmount := 0.0
	if evt.Amount > 100000 {
		highValueAmount = 1.0
	}

	recentFailures := float64(state.GetDebitAttempts(evt.ID))

	z := (isSalaryWindow * 0.8) + (highValueAmount * 0.5) + (recentFailures * -1.2) - 0.4
	
	if action == domain.ActionNudge {
		z -= 0.5 
	} else if action == domain.ActionRetryAlt {
		z += 0.2 
	} else if action == domain.ActionSendPreDebitNotice {
		z += 0.8 
	} else if action == domain.ActionSendDiscount5 {
		z += 1.0 // Discounts heavily boost conversion
	} else if action == domain.ActionSendDiscount10 {
		z += 2.0 // Deeper discounts boost conversion more
	} else if action == domain.ActionEscalateVoiceHinglish {
		z += 1.5 // Voice escalation boost
	}

	var pRecover float64
	if basePRecover != nil {
		pRecover = *basePRecover
		if action == domain.ActionNudge {
			pRecover -= 0.1
		} else if action == domain.ActionRetryAlt {
			pRecover += 0.05
		} else if action == domain.ActionSendPreDebitNotice {
			pRecover += 0.15
		} else if action == domain.ActionSendDiscount5 {
			pRecover += 0.30
		} else if action == domain.ActionSendDiscount10 {
			pRecover += 0.50
		} else if action == domain.ActionEscalateVoiceHinglish {
			pRecover += 0.40
		}
		if pRecover > 1.0 { pRecover = 1.0 }
		if pRecover < 0.0 { pRecover = 0.0 }
	} else {
		pRecover = sigmoid(z)
	}

	var actionCost int64 = 0
	var churnProb float64 = 0.0

	recoverablePrincipal := float64(evt.Amount)
	switch action {
	case domain.ActionRetrySame, domain.ActionRetryAlt:
		actionCost = 50
		churnProb = 0.0
	case domain.ActionNudge:
		actionCost = 100
		churnProb = 0.05
	case domain.ActionSendPreDebitNotice:
		actionCost = 10
		churnProb = 0.01
	case domain.ActionSendDiscount5:
		actionCost = 50 // Delivery cost for SMS/Email
		recoverablePrincipal = float64(evt.Amount) * 0.95
		churnProb = 0.0
	case domain.ActionSendDiscount10:
		actionCost = 50 // Delivery cost for SMS/Email
		recoverablePrincipal = float64(evt.Amount) * 0.90
		churnProb = 0.0
	case domain.ActionEscalateVoiceHinglish:
		actionCost = 250 // Cost of Interactive Voice AI
		churnProb = 0.0
	}

	ev := (pRecover * recoverablePrincipal) - float64(actionCost) - (churnProb * float64(evt.LTV))
	return pRecover, int64(math.Round(ev))
}






