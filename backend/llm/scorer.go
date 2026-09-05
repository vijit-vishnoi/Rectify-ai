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

type RecoveryScore struct {
	PRecover   float64 `json:"p_recover"`
	Confidence float64 `json:"confidence"`
	Reason     string  `json:"reason"`
}

func InferRecoveryProbability(amount int64, errorCode string, attempts int) (float64, error) {
	if !GlobalBreaker.AllowRequest() {
		log.Println("[BREAKER] Fast-failing Scorer LLM request. Circuit open.")
		return 0.0, errors.New("circuit breaker open")
	}

	apiKey := os.Getenv("GROQ_API_KEY")
	if apiKey == "" {
		GlobalBreaker.RecordFailure()
		return 0.0, errors.New("GROQ_API_KEY environment variable is not set")
	}

	sysPrompt := `You are a fintech risk assessment AI. Analyze the failed payment and predict the probability of successful recovery on a retry. Return ONLY a JSON object: {"p_recover": <float between 0.0 and 1.0>, "confidence": <float>, "reason": "<brief reason>"}.
Context: Hard failures like 'mandate_revoked' or 'suspected_fraud' should have a score near 0.0. Soft failures like 'insufficient_funds' should be higher, but decrease as 'attempts' increase.`

	userPrompt := fmt.Sprintf("Failed Payment Details:\nAmount: %d paise\nError Code: %s\nPrevious Attempts: %d", amount, errorCode, attempts)

	reqBody := map[string]interface{}{
		"model": "qwen/qwen3.8-27b",
		"messages": []map[string]string{
			{"role": "system", "content": sysPrompt},
			{"role": "user", "content": userPrompt},
		},
		"response_format": map[string]string{"type": "json_object"},
	}

	jsonReq, _ := json.Marshal(reqBody)
	req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonReq))
	if err != nil {
		GlobalBreaker.RecordFailure()
		return 0.0, err
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
		return 0.0, err
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		GlobalBreaker.RecordFailure()
		bodyBytes, _ := io.ReadAll(res.Body)
		return 0.0, fmt.Errorf("Groq rejected payload: %s", string(bodyBytes))
	}

	var llmRes groqResponse
	if err := json.NewDecoder(res.Body).Decode(&llmRes); err != nil || len(llmRes.Choices) == 0 {
		GlobalBreaker.RecordFailure()
		return 0.0, errors.New("failed to decode LLM response")
	}

	var finalResult RecoveryScore
	if err := json.Unmarshal([]byte(llmRes.Choices[0].Message.Content), &finalResult); err != nil {
		GlobalBreaker.RecordFailure()
		return 0.0, errors.New("LLM did not return valid RecoveryScore JSON")
	}

	GlobalBreaker.RecordSuccess()
	log.Printf("[LLM SCORER] p_recover: %.2f | reason: %s", finalResult.PRecover, finalResult.Reason)
	return finalResult.PRecover, nil
}


func GenerateHinglishScript(amount int64, reason string) (string, error) {
	fallbackScript := fmt.Sprintf("Namaste! Rectify AI se baat kar rahi hoon. Aapka %d INR ka payment '%s' ki wajah se fail ho gaya hai. Kripya apna account check karein aur payment complete karein.", amount/100, reason)
	
	apiKey := os.Getenv("GROQ_API_KEY")
	if apiKey == "" {
		return fallbackScript, nil
	}

	sysPrompt := `You are a conversational AI recovery agent for a fintech company. Generate exactly a 2-sentence natural Hinglish script to politely inform the user about a failed payment and ask them to complete it. Do not include quotes or extra text. Mention the amount and reason context.`
	userPrompt := fmt.Sprintf("Failed Payment Amount: %d INR, Reason: %s", amount/100, reason)

	reqBody := map[string]interface{}{
		"model": "qwen/qwen3.8-27b",
		"messages": []map[string]string{
			{"role": "system", "content": sysPrompt},
			{"role": "user", "content": userPrompt},
		},
	}

	jsonReq, _ := json.Marshal(reqBody)
	req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonReq))
	if err != nil {
		return fallbackScript, nil
	}
	
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 5 * time.Second}
	res, err := client.Do(req)
	if err != nil || res.StatusCode != 200 {
		return fallbackScript, nil
	}
	defer res.Body.Close()

	var result struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	
	bodyBytes, _ := io.ReadAll(res.Body)
	if err := json.Unmarshal(bodyBytes, &result); err != nil {
		return fallbackScript, nil
	}
	
	if len(result.Choices) > 0 && result.Choices[0].Message.Content != "" {
		return result.Choices[0].Message.Content, nil
	}

	return fallbackScript, nil
}
