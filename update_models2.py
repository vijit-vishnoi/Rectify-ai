import re
with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = """type MemoryState struct {
	mu                   sync.RWMutex
	ledger               []LedgerRecord
	events               map[string]Event
	debitAttempts        map[string]int
	historicalAttempts   map[string]int
	settledStatus        map[string]bool
	ProcessedEvents      sync.Map
	PreDebitNoticeSentAt map[string]*time.Time
	PromiseToPayExpiry   map[string]*time.Time
}"""

replacement1 = """type MemoryState struct {
	mu                   sync.RWMutex
	ledger               []LedgerRecord
	events               map[string]Event
	debitAttempts        map[string]int
	historicalAttempts   map[string]int
	settledStatus        map[string]bool
	ProcessedEvents      sync.Map
	PreDebitNoticeSentAt map[string]*time.Time
	PromiseToPayExpiry   map[string]*time.Time

	metricsMu      sync.RWMutex
	totalAtRisk    int64
	totalRecovered int64
	totalCost      int64
}"""

c = c.replace(target1, replacement1)

target2 = """func (s *MemoryState) SetPreDebitNoticeSentAt(id string, t time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.PreDebitNoticeSentAt[id] = &t
}"""

replacement2 = """func (s *MemoryState) SetPreDebitNoticeSentAt(id string, t time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.PreDebitNoticeSentAt[id] = &t
}

func (s *MemoryState) AddAtRisk(amount int64) {
	s.metricsMu.Lock()
	defer s.metricsMu.Unlock()
	s.totalAtRisk += amount
}

func (s *MemoryState) AddRecovered(amount int64) {
	s.metricsMu.Lock()
	defer s.metricsMu.Unlock()
	s.totalRecovered += amount
}

func (s *MemoryState) AddCost(cost int64) {
	s.metricsMu.Lock()
	defer s.metricsMu.Unlock()
	s.totalCost += cost
}

func (s *MemoryState) GetMetrics() map[string]int64 {
	s.metricsMu.RLock()
	defer s.metricsMu.RUnlock()
	return map[string]int64{
		"total_at_risk":   s.totalAtRisk,
		"total_recovered": s.totalRecovered,
		"total_cost":      s.totalCost,
	}
}"""

c = c.replace(target2, replacement2)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'w', encoding='utf-8') as f:
    f.write(c)
