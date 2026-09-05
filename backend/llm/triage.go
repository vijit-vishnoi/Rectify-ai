package llm

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"
)

type TriageResult struct {
	FailureClass string `json:"failure_class"`
	Reasoning    string `json:"reasoning"`
}

type groqResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

func TriageErrorCode(rawCode, rawMessage string) (*TriageResult, error) {
	if !GlobalBreaker.AllowRequest() {
		log.Println("[BREAKER] Fast-failing LLM request. Fallback classification applied.")
		return &TriageResult{
			FailureClass: "temporary_failure",
			Reasoning:    "Circuit breaker open, fallback applied.",
		}, nil
	}

	apiKey := os.Getenv("GROQ_API_KEY")
	if apiKey == "" {
		GlobalBreaker.RecordFailure()
		return nil, errors.New("GROQ_API_KEY environment variable is not set")
	}

	prompt := fmt.Sprintf(`You are a payment triage AI. Analyze this gateway error: "%s" - "%s".
Map it to EXACTLY one of these standard classes: insufficient_funds, mandate_revoked, suspected_fraud, or temporary_failure.
Respond ONLY with a JSON object containing "failure_class" and "reasoning" keys. Do not include markdown formatting.`, rawCode, rawMessage)

	reqBody := map[string]interface{}{
		"model": "qwen/qwen3.8-27b",
		"messages": []map[string]string{
			{"role": "system", "content": "You output only raw, valid JSON."},
			{"role": "user", "content": prompt},
		},
		"response_format": map[string]string{"type": "json_object"},
	}

	jsonReq, _ := json.Marshal(reqBody)
	req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonReq))
	if err != nil {
		GlobalBreaker.RecordFailure()
		return nil, err
	}
	
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	timeoutDur := 5 * time.Second
	timeoutMsStr := os.Getenv("TEST_TIMEOUT_MS")
	if timeoutMsStr != "" {
		ms, _ := strconv.Atoi(timeoutMsStr)
		if ms > 0 {
			timeoutDur = time.Duration(ms) * time.Millisecond
		}
	}

	client := &http.Client{Timeout: timeoutDur}
	res, err := client.Do(req)
	if err != nil {
		GlobalBreaker.RecordFailure()
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		GlobalBreaker.RecordFailure()
		bodyBytes, _ := io.ReadAll(res.Body)
		return nil, fmt.Errorf("Groq rejected payload: %s", string(bodyBytes))
	}

	var llmRes groqResponse
	if err := json.NewDecoder(res.Body).Decode(&llmRes); err != nil || len(llmRes.Choices) == 0 {
		GlobalBreaker.RecordFailure()
		return nil, errors.New("failed to decode LLM response")
	}

	var finalResult TriageResult
	if err := json.Unmarshal([]byte(llmRes.Choices[0].Message.Content), &finalResult); err != nil {
		GlobalBreaker.RecordFailure()
		return nil, errors.New("LLM did not return valid TriageResult JSON")
	}

	GlobalBreaker.RecordSuccess()
	return &finalResult, nil
}
