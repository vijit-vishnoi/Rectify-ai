package llm

import (
	"log"
	"sync"
	"time"
)

type BreakerState int

const (
	StateClosed BreakerState = iota
	StateOpen
	StateHalfOpen
)

const (
	MaxFailures = 3
	Cooldown    = 10 * time.Second
)

type CircuitBreaker struct {
	mu                  sync.Mutex
	State               BreakerState
	ConsecutiveFailures int
	LastFailureTime     time.Time
}

var GlobalBreaker = &CircuitBreaker{
	State:               StateClosed,
	ConsecutiveFailures: 0,
}

func (cb *CircuitBreaker) AllowRequest() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.State {
	case StateClosed:
		return true
	case StateOpen:
		if time.Since(cb.LastFailureTime) >= Cooldown {
			cb.State = StateHalfOpen
			log.Println("[BREAKER] State transition: OPEN -> HALF-OPEN. Probing LLM...")
			return true
		}
		return false
	case StateHalfOpen:
		return false
	}
	return true
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	if cb.State != StateClosed {
		log.Println("[BREAKER] State transition: HALF-OPEN -> CLOSED. LLM recovered.")
	}
	cb.State = StateClosed
	cb.ConsecutiveFailures = 0
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.ConsecutiveFailures++
	cb.LastFailureTime = time.Now()

	if cb.State == StateHalfOpen {
		cb.State = StateOpen
		log.Println("[BREAKER] Probe failed. State transition: HALF-OPEN -> OPEN")
	} else if cb.State == StateClosed {
		if cb.ConsecutiveFailures >= MaxFailures {
			cb.State = StateOpen
			log.Printf("[BREAKER] Max failures (%d) reached. State transition: CLOSED -> OPEN\n", MaxFailures)
		}
	}
}
