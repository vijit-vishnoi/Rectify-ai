with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

old_ledger = """		log.Printf("[DIAGNOSTIC] Step 4 - Location: main.go creating LedgerRecord, value = %f", bestPRecover)
		record := domain.LedgerRecord{"""

new_ledger = """		if finalAction != domain.ActionStop && finalAction != domain.ActionWait {
			state.IncrementHistoricalAttempts(evt.ID)
		}

		log.Printf("[DIAGNOSTIC] Step 4 - Location: main.go creating LedgerRecord, value = %f", bestPRecover)
		record := domain.LedgerRecord{"""

c = c.replace(old_ledger, new_ledger)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
