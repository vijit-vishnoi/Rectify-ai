#!/bin/bash

# Configuration
SECRET="hwk_test_secret_123"
URL="http://localhost:8080/webhook"
TIMESTAMP=$(date +%s)

# Minified JSON payload to avoid newline hashing discrepancies
PAYLOAD='{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_test_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","error_reason":"Insufficient balance","created_at":'$TIMESTAMP'}}}}'

# Generate HMAC SHA256 Signature
VALID_SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
INVALID_SIG="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

echo "----------------------------------------"
echo "1. Testing VALID Signature"
echo "----------------------------------------"
curl -s -w "HTTP Status: %{http_code}\n" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: $VALID_SIG" \
  -d "$PAYLOAD"

echo -e "\n----------------------------------------"
echo "2. Testing INVALID Signature"
echo "----------------------------------------"
curl -s -w "HTTP Status: %{http_code}\n" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: $INVALID_SIG" \
  -d "$PAYLOAD"