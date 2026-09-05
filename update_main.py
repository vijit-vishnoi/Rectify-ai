import re
with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add "math/rand"
c = c.replace('"math"', '"math"\n\t"math/rand"')

# 2. Add /batch/simulate and /metrics
endpoints = """	r.Post("/batch/simulate", func(w http.ResponseWriter, r *http.Request) {
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
				amt := int64((rand.Intn(40) + 10) * 100) // ?10.00 to ?50.00
				evt := domain.Event{
					ID:         fmt.Sprintf("pay_batch_%d_%d", time.Now().UnixNano(), i),
					Amount:     amt,
					ErrorCode:  errorCodes[rand.Intn(len(errorCodes))],
					OccurredAt: time.Now().Add(time.Duration(-rand.Intn(72)) * time.Hour),
					LTV:        1000000,
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

	r.Get("/ledger", func(w http.ResponseWriter, r *http.Request) {"""

c = c.replace('	r.Get("/ledger", func(w http.ResponseWriter, r *http.Request) {', endpoints)

# 3. Add fmt import if needed
if '"fmt"' not in c:
    c = c.replace('"math"', '"fmt"\n\t"math"')

# 4. Update processEvents with Metrics Tracking
target_record = """		log.Printf("[DIAGNOSTIC] Step 4 - Location: main.go creating LedgerRecord, value = %f", bestPRecover)
		record := domain.LedgerRecord{"""

replacement_record = """		if state.GetHistoricalAttemptCount(evt.ID) == 0 {
			state.AddAtRisk(evt.Amount)
		}

		var cost int64 = 0
		if finalAction == domain.ActionSendPreDebitNotice {
			cost = 500
		} else if finalAction == domain.ActionNudge {
			cost = 100
		}
		if cost > 0 {
			state.AddCost(cost)
		}

		if finalAction == domain.ActionRetrySame || finalAction == domain.ActionRetryAlt {
			r := rand.Float64()
			if r <= bestPRecover {
				state.MarkSettled(evt.ID)
				state.AddRecovered(evt.Amount)
				log.Printf("[SIMULATION WIN] AI recovered %d paise on %s!", evt.Amount, evt.ID)
			}
		}

		log.Printf("[DIAGNOSTIC] Step 4 - Location: main.go creating LedgerRecord, value = %f", bestPRecover)
		record := domain.LedgerRecord{"""

c = c.replace(target_record, replacement_record)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'w', encoding='utf-8') as f:
    f.write(c)
