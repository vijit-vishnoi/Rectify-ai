import re

with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'r', encoding='utf-8') as f:
    c = f.read()

target = """  			for i := 0; i < payload.Count; i++ {
  				amt := int64((rand.Intn(40) + 10) * 100) // ?10.00 to ?50.00
  				evt := domain.Event{
  					ID:         fmt.Sprintf("pay_batch_%d_%d", time.Now().UnixNano(), i),
  					Amount:     amt,
  					ErrorCode:  errorCodes[rand.Intn(len(errorCodes))],
  					OccurredAt: time.Now().Add(time.Duration(-rand.Intn(72)) * time.Hour),
  					LTV:        1000000,
  				}
  				eventChan <- evt
  			}"""

replacement = """			for i := 0; i < payload.Count; i++ {
				// Generate amounts from ?500.00 to ?5,000.00 to ensure EV math is highly positive
				amt := int64((rand.Intn(450) + 50) * 1000) 
				evt := domain.Event{
					ID:         fmt.Sprintf("pay_batch_%d_%d", time.Now().UnixNano(), i),
					Amount:     amt,
					ErrorCode:  errorCodes[rand.Intn(len(errorCodes))],
					OccurredAt: time.Now().Add(time.Duration(-rand.Intn(72)) * time.Hour),
					LTV:        1000000,
				}
				
				// Bypass cold-start and RBI for half the events to simulate mature payment histories
				if rand.Float32() > 0.5 {
					state.SaveEvent(evt) // Increments attempt to 1
					state.SetPreDebitNoticeSentAt(evt.ID, time.Now().Add(-25 * time.Hour))
				}
				
				eventChan <- evt
			}"""

c = c.replace(target, replacement)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'w', encoding='utf-8') as f:
    f.write(c)
