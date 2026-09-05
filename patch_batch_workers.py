with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

# Replace the single loop in processEvents with a worker pool
old_func_start = """func processEvents(events <-chan domain.Event, state *domain.MemoryState) {
	for evt := range events {"""

new_func_start = """func processEvents(events <-chan domain.Event, state *domain.MemoryState) {
	const numWorkers = 10
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for evt := range events {"""

c = c.replace(old_func_start, new_func_start)

# Add closing braces for the worker pool
old_func_end = """		state.AppendLedger(record)
		log.Printf("[LEDGER] Appended Seq %d | Action: %s | EV: %d | Hash: %s", record.Seq, record.ActionTaken, record.ExpectedVal, record.Hash[:16]+"...")
	}
}"""

new_func_end = """		state.AppendLedger(record)
		log.Printf("[WORKER %d] [LEDGER] Appended Seq %d | Action: %s | EV: %d | Hash: %s", workerID, record.Seq, record.ActionTaken, record.ExpectedVal, record.Hash[:16]+"...")
			}
		}(i)
	}
	wg.Wait()
}"""
c = c.replace(old_func_end, new_func_end)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
