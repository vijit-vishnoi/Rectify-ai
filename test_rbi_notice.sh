#!/bin/bash
SECRET="hwk_test_secret_123"
URL="http://localhost:8080/webhook"
TIMESTAMP=$(date +%s)
EVENT_ID="evt_rbi_test_001"
PAYLOAD='{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_rbi_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","created_at":'$TIMESTAMP'}}}}'
VALID_SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
curl -s -X POST "$URL" -H "Content-Type: application/json" -H "X-Razorpay-Signature: $VALID_SIG" -H "x-razorpay-event-id: $EVENT_ID" -d "$PAYLOAD"
