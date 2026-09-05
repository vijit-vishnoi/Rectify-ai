with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

# Add discount recovery simulation alongside retry recovery simulation
old_recovery = """		if finalAction == domain.ActionRetrySame || finalAction == domain.ActionRetryAlt {
			r := rand.Float64()
			if r <= bestPRecover {
				state.MarkSettled(evt.ID)
				state.AddRecovered(evt.Amount)
				log.Printf("[SIMULATION WIN] AI recovered %d paise on %s!", evt.Amount, evt.ID)
			}
		}"""
new_recovery = """		if finalAction == domain.ActionRetrySame || finalAction == domain.ActionRetryAlt {
			r := rand.Float64()
			if r <= bestPRecover {
				state.MarkSettled(evt.ID)
				state.AddRecovered(evt.Amount)
				log.Printf("[SIMULATION WIN] AI recovered %d paise on %s!", evt.Amount, evt.ID)
			}
		}

		// Simulate checkout discount recovery
		if finalAction == domain.ActionSendDiscount5 || finalAction == domain.ActionSendDiscount10 {
			r := rand.Float64()
			if r <= bestPRecover {
				var recovered int64
				if finalAction == domain.ActionSendDiscount5 {
					recovered = int64(float64(evt.Amount) * 0.95)
				} else {
					recovered = int64(float64(evt.Amount) * 0.90)
				}
				state.MarkSettled(evt.ID)
				state.AddRecovered(recovered)
				log.Printf("[SIMULATION WIN] Checkout recovered %d paise (discounted) on %s!", recovered, evt.ID)
			}
		}"""
c = c.replace(old_recovery, new_recovery)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
