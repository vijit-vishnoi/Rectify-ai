#!/bin/bash

# Configuration
SECRET="hwk_test_secret_123"
URL="http://localhost:8080/webhook"
TIMESTAMP=$(date +%s)
EVENT_ID="evt_test_dup_999"

# Minified JSON payload to avoid newline hashing discrepancies
PAYLOAD='{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_test_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","error_reason":"Insufficient balance","created_at":'$TIMESTAMP'}}}}'

# Generate HMAC SHA256 Signature
VALID_SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')

echo "----------------------------------------"
echo "Firing First Webhook (Should Process)"
echo "----------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: $VALID_SIG" \
  -H "x-razorpay-event-id: $EVENT_ID" \
  -d "$PAYLOAD"

echo -e "\n----------------------------------------"
echo "Firing Second Webhook (Should Drop)"
echo "----------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: $VALID_SIG" \
  -H "x-razorpay-event-id: $EVENT_ID" \
  -d "$PAYLOAD"
