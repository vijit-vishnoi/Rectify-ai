package domain

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

type EventType string

const (
	EventTypePaymentFailed     EventType = "payment.failed"
	EventTypePromiseToPay      EventType = "promise_to_pay"
	EventTypeCheckoutAbandoned EventType = "checkout.abandoned"
)

type Event struct {
	ID           string    `json:"id"`
	Type         EventType `json:"type"`
	Amount       int64     `json:"amount"`
	ErrorCode    string    `json:"error_code"`
	OccurredAt   time.Time `json:"created_at"`
	LTV          int64     `json:"ltv,omitempty"`
	TraiQuietHours bool      `json:"simulate_trai,omitempty"`
	FastForward24h bool      `json:"fast_forward_24h,omitempty"`
}

type RazorpayPaymentEntity struct {
	ID          string `json:"id"`
	Amount      int64  `json:"amount"`
	PromiseDate int64  `json:"promise_date,omitempty"`
	Currency    string `json:"currency"`
	Status      string `json:"status"`
	ErrorCode   string `json:"error_code"`
	ErrorReason string `json:"error_reason"`
	CreatedAt   int64  `json:"created_at"`
}

type RazorpayPayload struct {
	Payment struct {
		Entity RazorpayPaymentEntity `json:"entity"`
	} `json:"payment"`
}

type RazorpayWebhook struct {
	Event          EventType       `json:"event"`
	AccountID      string          `json:"account_id"`
	Payload        RazorpayPayload `json:"payload"`
	FastForward24h bool            `json:"fast_forward_24h,omitempty"`
	TraiQuietHours bool            `json:"trai_quiet_hours,omitempty"`
}

type Action string

const (
	ActionRetrySame          Action = "RETRY_SAME_RAIL"
	ActionRetryAlt           Action = "RETRY_ALT_RAIL"
	ActionNudge              Action = "SEND_NUDGE"
	ActionSendPreDebitNotice Action = "SEND_PRE_DEBIT_NOTICE"
	ActionEscalateVoiceHinglish Action = "ESCALATE_VOICE_HINGLISH"
	ActionDispatchVoiceAgent Action = "DISPATCH_VOICE_AGENT"
	ActionEscalateHuman      Action = "ESCALATE_HUMAN"
	ActionWait               Action = "WAIT"
	ActionPromiseLogged      Action = "PROMISE_LOGGED"
	ActionPromisePending     Action = "PROMISE_PENDING"
	ActionStop               Action = "STOP"

	// Checkout Drop-off Recovery Actions
	ActionSendDiscount5  Action = "SEND_DISCOUNT_5"
	ActionSendDiscount10 Action = "SEND_DISCOUNT_10"
)

// LedgerRecord is a single immutable block in the hash-chained audit ledger.
type LedgerRecord struct {
	Seq          int       `json:"seq"`
	Timestamp    time.Time `json:"timestamp"`
	EventID      string    `json:"event_id"`
	AttemptCount int       `json:"attempt_count"`
	ActionTaken  Action    `json:"action_taken"`
	ExpectedVal  int64     `json:"expected_value"`
	PRecover     float64   `json:"p_recover"`
	LLMReasoning string    `json:"llm_reasoning,omitempty"`
	VoiceScript  string    `json:"voice_script,omitempty"`
	Hash         string    `json:"hash"`
	PreviousHash string    `json:"previous_hash"`
}

func (r *LedgerRecord) ComputeHash() string {
	data := fmt.Sprintf("%d|%s|%s|%d|%s|%d|%f|%s|%s",
		r.Seq, r.Timestamp.Format(time.RFC3339Nano), r.EventID,
		r.AttemptCount, r.ActionTaken, r.ExpectedVal, r.PRecover, r.VoiceScript, r.PreviousHash)
	h := sha256.Sum256([]byte(data))
	return hex.EncodeToString(h[:])
}

// MemoryState holds all in-memory state with mutex protection for concurrency safety.
type MemoryState struct {
	mu                 sync.RWMutex
	processedEvents    map[string]bool
	settledPayments    map[string]bool
	promisesToPay      map[string]time.Time
	preDebitNotices    map[string]time.Time
	historicalAttempts map[string]int
	totalAtRisk        float64
	totalRecovered     float64
	totalCost          float64
	ledger             []LedgerRecord
	events             []Event
}

func NewMemoryState() *MemoryState {
	return &MemoryState{
		processedEvents:    make(map[string]bool),
		settledPayments:    make(map[string]bool),
		promisesToPay:      make(map[string]time.Time),
		preDebitNotices:    make(map[string]time.Time),
		historicalAttempts: make(map[string]int),
	}
}

// --- Idempotency ---

func (m *MemoryState) HasProcessedEvent(id string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.processedEvents[id]
}

func (m *MemoryState) MarkEventProcessed(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.processedEvents[id] = true
}

// --- Settlement ---

func (m *MemoryState) IsSettled(id string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.settledPayments[id]
}

func (m *MemoryState) MarkSettled(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.settledPayments[id] = true
}

// --- Promise to Pay ---

func (m *MemoryState) RecordPromiseToPay(id string, expiry time.Time) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.promisesToPay[id] = expiry
}

func (m *MemoryState) HasActivePromiseToPay(id string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	expiry, exists := m.promisesToPay[id]
	return exists && time.Now().Before(expiry)
}

// --- Pre-Debit Notice (RBI) ---

func (m *MemoryState) SetPreDebitNoticeSentAt(id string, t time.Time) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.preDebitNotices[id] = t
}

func (m *MemoryState) HasEverSentPreDebitNotice(id string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	_, exists := m.preDebitNotices[id]
	return exists
}

func (m *MemoryState) HasValidPreDebitNotice(id string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	sentAt, exists := m.preDebitNotices[id]
	if !exists {
		return false
	}
	return time.Since(sentAt) >= 24*time.Hour
}

// --- Attempt Tracking ---

func (m *MemoryState) GetDebitAttempts(id string) int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.historicalAttempts[id]
}

func (m *MemoryState) GetHistoricalAttemptCount(id string) int {
	return m.GetDebitAttempts(id)
}

func (m *MemoryState) IncrementHistoricalAttempts(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.historicalAttempts[id]++
}

// --- Aggregate Metrics (Thread-Safe) ---

func (m *MemoryState) AddAtRisk(amount float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.totalAtRisk += amount
}

func (m *MemoryState) AddRecovered(amount float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.totalRecovered += amount
}

func (m *MemoryState) AddCost(cost float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.totalCost += cost
}

func (m *MemoryState) TotalAtRisk() float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.totalAtRisk
}

func (m *MemoryState) TotalRecovered() float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.totalRecovered
}

func (m *MemoryState) TotalCost() float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.totalCost
}

func (m *MemoryState) GetMetrics() map[string]float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return map[string]float64{
		"total_at_risk":  m.totalAtRisk,
		"total_recovered": m.totalRecovered,
		"total_cost":      m.totalCost,
	}
}

// --- Event Storage ---

func (m *MemoryState) SaveEvent(evt Event) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.events = append(m.events, evt)
}

// --- Ledger (Hash-Chained) ---

func (m *MemoryState) GetLedger() []LedgerRecord {
	m.mu.RLock()
	defer m.mu.RUnlock()
	out := make([]LedgerRecord, len(m.ledger))
	copy(out, m.ledger)
	return out
}

func (m *MemoryState) AppendLedger(record LedgerRecord) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.ledger = append(m.ledger, record)
}

func (m *MemoryState) GetNextSeq() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.ledger)
}

func (m *MemoryState) GetLastHash() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if len(m.ledger) == 0 {
		return "genesis"
	}
	return m.ledger[len(m.ledger)-1].Hash
}

func (m *MemoryState) VerifyChain() (bool, int) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	for i, block := range m.ledger {
		recomputed := block.ComputeHash()
		if recomputed != block.Hash {
			return false, i
		}
		if i > 0 && block.PreviousHash != m.ledger[i-1].Hash {
			return false, i
		}
	}
	return true, len(m.ledger)
}
