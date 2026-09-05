package main

import (
	"net/url"
	"sync"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"log"
	"fmt"
	"math"
	"math/rand"
	"net/http"
	"os"
	"time"
	"github.com/joho/godotenv"
	"rectify-ai-backend/domain"
	"rectify-ai-backend/engine"
	"rectify-ai-backend/llm"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

var ShadowModeEnabled = os.Getenv("SHADOW_MODE") == "true"

func GetLegacyRulebookAction(evt domain.Event, state *domain.MemoryState) domain.Action {
	if state.GetDebitAttempts(evt.ID) >= 3 {
		return domain.ActionStop
	}
	return domain.ActionRetrySame
}

func verifyRazorpaySignature(body []byte, signature, secret string) bool {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expectedSignature := hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(expectedSignature), []byte(signature))
}

func main() {
	_ = godotenv.Load()
	state := domain.NewMemoryState()
	secret := os.Getenv("RAZORPAY_WEBHOOK_SECRET")
	if secret == "" {
		secret = "hwk_test_secret_123"
	}

	r := chi.NewRouter()

	r.Use(middleware.Recoverer)

	r.Get("/tts", func(w http.ResponseWriter, req *http.Request) {
		text := req.URL.Query().Get("text")
		if text == "" {
			http.Error(w, "missing text parameter", http.StatusBadRequest)
			return
		}

		escapedText := url.QueryEscape(text)
		ttsURL := fmt.Sprintf("https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=%s&tl=hi", escapedText)

		ttsReq, err := http.NewRequest("GET", ttsURL, nil)
		if err != nil {
			http.Error(w, "failed to create request", http.StatusInternalServerError)
			return
		}
		ttsReq.Header.Set("User-Agent", "Mozilla/5.0")

		client := &http.Client{}
		resp, err := client.Do(ttsReq)
		if err != nil {
			http.Error(w, "failed to fetch audio", http.StatusBadGateway)
			return
		}
		defer resp.Body.Close()

		w.Header().Set("Content-Type", "audio/mpeg")
		io.Copy(w, resp.Body)
	})

	go engine.GlobalConfig.WatchConfig("policies/default.toml")
eventChan := make(chan domain.Event, 1000)
	go processEvents(eventChan, state)

	r.Post("/promise", func(w http.ResponseWriter, r *http.Request) {
		var payload struct {
			ID         string `json:"id"`
			HoursValid int    `json:"hours_valid"`
		}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		expiry := time.Now().Add(time.Duration(payload.HoursValid) * time.Hour)
		state.RecordPromiseToPay(payload.ID, expiry)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":     "recorded",
			"id":         payload.ID,
			"expires_at": expiry,
		})
	})

	r.Post("/webhook", func(w http.ResponseWriter, r *http.Request) {
		eventID := r.Header.Get("x-razorpay-event-id")
		if eventID != "" {
			if state.HasProcessedEvent(eventID) {
				log.Printf("[INGEST] Duplicate event dropped: %s", eventID)
				w.WriteHeader(http.StatusOK)
				return
			}
			state.MarkEventProcessed(eventID)
		}

		body, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "Failed to read body", http.StatusBadRequest)
			return
		}

		signature := r.Header.Get("X-Razorpay-Signature")
		if !verifyRazorpaySignature(body, signature, secret) {
			http.Error(w, "Invalid signature", http.StatusUnauthorized)
			return
		}

		var payload domain.RazorpayWebhook
		if err := json.Unmarshal(body, &payload); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		if payload.Event == domain.EventTypePromiseToPay {
			id := payload.Payload.Payment.Entity.ID
			promiseDate := payload.Payload.Payment.Entity.PromiseDate
			if promiseDate > 0 {
				expiry := time.Unix(promiseDate, 0)
				state.RecordPromiseToPay(id, expiry)
				log.Printf("[PROMISE] Recorded promise for %s until %v", id, expiry)
				
				// Append block to the ledger
				record := domain.LedgerRecord{
					Seq:          state.GetNextSeq(),
					Timestamp:    time.Now().UTC(),
					EventID:      id,
					AttemptCount: state.GetHistoricalAttemptCount(id),
					ActionTaken:  domain.ActionPromiseLogged,
					ExpectedVal:  0,
					PRecover:     0.0,
					Hash:         "",
					PreviousHash: state.GetLastHash(),
				}
				record.Hash = record.ComputeHash()
				state.AppendLedger(record)
				
				w.WriteHeader(http.StatusOK)
				return
			}
		}
		if payload.Event == domain.EventType("order.paid") || payload.Event == domain.EventType("subscription.charged") {
			id := payload.Payload.Payment.Entity.ID
			if id != "" {
				state.MarkSettled(id)
				log.Printf("[INGEST] Marked %s as settled from %s", id, payload.Event)
			}
			w.WriteHeader(http.StatusOK)
			return
		}

		if payload.Event != domain.EventTypePaymentFailed && payload.Event != domain.EventTypeCheckoutAbandoned {
			w.WriteHeader(http.StatusOK)
			return
		}

		entity := payload.Payload.Payment.Entity

		if payload.FastForward24h {
			pastTime := time.Now().Add(-25 * time.Hour)
			state.SetPreDebitNoticeSentAt(entity.ID, pastTime)
			log.Printf("[SIMULATOR] Fast-forwarded PreDebitNoticeTime for %s by 24h to bypass RBI guardrail", entity.ID)
		}
				evt := domain.Event{
			ID:         entity.ID,
			Type:       payload.Event,
			Amount:     entity.Amount,
			ErrorCode:  entity.ErrorCode,
			OccurredAt: time.Unix(entity.CreatedAt, 0),
			LTV:        1000000, 
			TraiQuietHours: payload.TraiQuietHours,
			FastForward24h: payload.FastForward24h,
		}

		eventChan <- evt
		w.WriteHeader(http.StatusAccepted)
		w.Write([]byte(`{"status":"accepted"}`))
	})

	r.Post("/batch/simulate", func(w http.ResponseWriter, r *http.Request) {
		var payload struct {
			Count int `json:"count"`
		}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		go func() {
			errorCodes := []string{"insufficient_funds", "temporary_failure", "mandate_revoked"}
			for i := 0; i < payload.Count; i++ {
				amt := int64((rand.Intn(450) + 50) * 1000)
				
				evt := domain.Event{
					ID:         fmt.Sprintf("pay_batch_%d_%d", time.Now().UnixNano(), i),
					Amount:     amt,
					ErrorCode:  errorCodes[rand.Intn(len(errorCodes))],
					OccurredAt: time.Now().Add(time.Duration(-rand.Intn(72)) * time.Hour),
					LTV:        1000000,
				}
				if rand.Float32() > 0.5 {
					state.IncrementHistoricalAttempts(evt.ID)
					state.SetPreDebitNoticeSentAt(evt.ID, time.Now().Add(-25 * time.Hour))
				}
				if rand.Float32() > 0.5 {
					state.IncrementHistoricalAttempts(evt.ID)
					state.SetPreDebitNoticeSentAt(evt.ID, time.Now().Add(-25 * time.Hour))
				}
				eventChan <- evt
			}
		}()

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{"status": "batch_started", "count": payload.Count})
	})

	r.Get("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		metrics := state.GetMetrics()
		
		// To display proper rupees instead of paise on the frontend, let's just send the exact paise and let frontend handle it.
		json.NewEncoder(w).Encode(metrics)
	})

	r.Get("/ledger", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		l := state.GetLedger()
		json.NewEncoder(w).Encode(l)
	})

	r.Get("/ledger/verify", func(w http.ResponseWriter, r *http.Request) {
		valid, blockChecked := state.VerifyChain()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"valid":          valid,
			"blocks_checked": blockChecked,
		})
	})

	
		r.Get("/tts", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			text := r.URL.Query().Get("text")
			if text == "" {
				http.Error(w, "missing text", http.StatusBadRequest)
				return
			}
			
			// Spoof User-Agent and strip Referer for Google TTS
			url := "https://translate.google.com/translate_tts?ie=UTF-8&q=" + url.QueryEscape(text) + "&tl=hi&client=tw-ob"
			
			req, err := http.NewRequest("GET", url, nil)
			if err != nil {
				http.Error(w, "failed to create req", http.StatusInternalServerError)
				return
			}
			req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
			
			client := &http.Client{}
			res, err := client.Do(req)
			if err != nil {
				http.Error(w, "failed to fetch tts", http.StatusInternalServerError)
				return
			}
			defer res.Body.Close()
			
			w.Header().Set("Content-Type", "audio/mpeg")
			io.Copy(w, res.Body)
		})

	log.Println("Starting Rectify AI on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func processEvents(events <-chan domain.Event, state *domain.MemoryState) {
	const numWorkers = 10
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for evt := range events {
		log.Printf("[ENGINE] Processing event %s for %d paise", evt.ID, evt.Amount)
		state.SaveEvent(evt)
		
		llmReason := ""
		if evt.ErrorCode == "unknown" || evt.ErrorCode == "" {
			res, err := llm.TriageErrorCode(evt.ErrorCode, "Unknown failure")
			if err == nil {
				evt.ErrorCode = res.FailureClass
				llmReason = res.Reasoning
			} else {
				log.Printf("[LLM ERROR] API Call Failed: %v\n", err)
			}
		}

		attempts := state.GetDebitAttempts(evt.ID)
		llmScore, err := llm.InferRecoveryProbability(evt.Amount, evt.ErrorCode, attempts)
		var pRecoverPtr *float64
		if err == nil {
			historicalAttempts := state.GetHistoricalAttemptCount(evt.ID)
			decayedProb := llmScore * math.Pow(0.75, float64(historicalAttempts))
			pRecoverPtr = &decayedProb
			if llmReason == "" {
				llmReason = "[Scorer] Dynamic P(Recover) assigned"
			}
		} else {
			log.Printf("[LLM SCORER ERROR] %v. Falling back to sigmoid math.", err)
		}

		candidates := engine.GenerateCandidates(evt)
				var bestAction domain.Action = domain.ActionStop
		var bestEV int64 = -1
		var bestPRecover float64 = 0.0
		var temporalVeto bool = false

		for _, action := range candidates {
			pRecover, ev := engine.ScoreCandidate(action, evt, state, pRecoverPtr)
			
			allowed, reason := engine.CheckGuardrails(state, evt, action)
			if !allowed {
                log.Printf("[DEBUG] Action %s vetoed by guardrails: %s", action, reason)
				if (action == domain.ActionRetrySame || action == domain.ActionRetryAlt) && (reason == "missing_rbi_pre_debit_notice" || reason == "active_promise_to_pay" || reason == "trai_quiet_hours") {
					temporalVeto = true
				}
				continue
			}

			if ev > bestEV {
				bestEV = ev
				bestAction = action
				bestPRecover = pRecover
			}
		}

		if bestEV < 0 {
			if temporalVeto {
				bestAction = domain.ActionWait
			} else {
				bestAction = domain.ActionStop
			}
		}

		finalAction := bestAction
		if ShadowModeEnabled {
			legacyAction := GetLegacyRulebookAction(evt, state)
			log.Printf("[SHADOW] AI proposed: %s | Executing Legacy: %s", bestAction, legacyAction)
			finalAction = legacyAction
		}

		if state.GetHistoricalAttemptCount(evt.ID) == 0 {
			state.AddAtRisk(float64(evt.Amount))
		}

		var cost int64 = 0
		if finalAction == domain.ActionSendPreDebitNotice {
			cost = 500
		} else if finalAction == domain.ActionNudge {
			cost = 100
		}
		if cost > 0 {
			state.AddCost(float64(cost))
		}

		if finalAction == domain.ActionRetrySame || finalAction == domain.ActionRetryAlt {
			_ = rand.Float64()
			if false { // DEMO RIG: Forced to always fail
				state.MarkSettled(evt.ID)
				state.AddRecovered(float64(evt.Amount))
				log.Printf("[SIMULATION WIN] AI recovered %d paise on %s!", evt.Amount, evt.ID)
			}
		}

		// Simulate checkout discount recovery
		if finalAction == domain.ActionSendDiscount5 || finalAction == domain.ActionSendDiscount10 {
			_ = rand.Float64()
			if false { // DEMO RIG: Forced to always fail
				var recovered int64
				if finalAction == domain.ActionSendDiscount5 {
					recovered = int64(float64(evt.Amount) * 0.95)
				} else {
					recovered = int64(float64(evt.Amount) * 0.90)
				}
				state.MarkSettled(evt.ID)
				state.AddRecovered(float64(recovered))
				log.Printf("[SIMULATION WIN] Checkout recovered %d paise (discounted) on %s!", recovered, evt.ID)
			}
		}

		
		var voiceScript string
		if finalAction == domain.ActionEscalateVoiceHinglish {
			script, _ := llm.GenerateHinglishScript(evt.Amount, evt.ErrorCode)
			voiceScript = script
		}

		record := domain.LedgerRecord{
			Seq:          state.GetNextSeq(),
			Timestamp:    time.Now().UTC(),
			EventID:      evt.ID,
			AttemptCount: attempts,
			ActionTaken:  finalAction,
			ExpectedVal:  bestEV,
			PRecover:     bestPRecover,
			LLMReasoning: llmReason,
			VoiceScript:  voiceScript,
			PreviousHash: state.GetLastHash(),
		}

		if finalAction != domain.ActionStop && finalAction != domain.ActionWait {
			state.IncrementHistoricalAttempts(evt.ID)
		}

		record.Hash = record.ComputeHash()
		
		state.AppendLedger(record)
		log.Printf("[WORKER %d] [LEDGER] Appended Seq %d | Action: %s | EV: %d | Hash: %s", workerID, record.Seq, record.ActionTaken, record.ExpectedVal, record.Hash[:16]+"...")
			}
		}(i)
	}
	wg.Wait()
}











