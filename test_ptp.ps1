$SECRET = "hwk_test_secret_123"
$URL_PROMISE = "http://localhost:8080/promise"
$URL_WEBHOOK = "http://localhost:8080/webhook"
$TIMESTAMP = [int][double]::Parse((Get-Date (Get-Date).ToUniversalTime() -UFormat %s))
$EVENT_ID = "pay_ptp_001"

# 1. Register Promise to Pay
$PTP_PAYLOAD = '{"id":"pay_ptp_001","hours_valid":48}'
Write-Host "Registering Promise-to-Pay (48h)..."
$r1 = Invoke-WebRequest -Uri $URL_PROMISE -Method Post -Body $PTP_PAYLOAD -ContentType "application/json" -UseBasicParsing
Write-Host "Response: $($r1.Content)"

Start-Sleep -Seconds 1

# 2. Fire failed webhook
$PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_ptp_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","created_at":' + $TIMESTAMP + '}}}}'

$hmac = new-object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
$hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
$VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

Write-Host "`nFiring payment.failed for $EVENT_ID..."
$r2 = Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"="evt_ptp_001"} -UseBasicParsing
Write-Host "Response: $($r2.Content)"
