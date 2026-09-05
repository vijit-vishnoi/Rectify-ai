$SECRET = "hwk_test_secret_123"
$URL_WEBHOOK = "http://localhost:8080/webhook"
$TIMESTAMP = [int][double]::Parse((Get-Date (Get-Date).ToUniversalTime() -UFormat %s))

$PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_dyn_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","created_at":' + $TIMESTAMP + '}}}}'

$hmac = new-object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
$hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
$VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

Write-Host "Step 1: Firing initial webhook (Should process)..."
$r1 = Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"="evt_dyn_001"} -UseBasicParsing
Write-Host "Response 1: $($r1.Content)"

Start-Sleep -Seconds 1

Write-Host "Step 2: Overwriting TOML to max_attempts = 0..."
$NEW_TOML = @"
[guardrails]
max_attempts = 0
max_age_days = 21
rbi_notice_hours = 24
"@
Set-Content -Path "d:\coding\PROJECTS\rectify-ai\backend\policies\default.toml" -Value $NEW_TOML

Write-Host "Step 3: Waiting for hot-reload..."
Start-Sleep -Seconds 3

Write-Host "Step 4: Firing second webhook for same entity (Should be vetoed by max_attempts=0)..."
$r2 = Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"="evt_dyn_002"} -UseBasicParsing
Write-Host "Response 2: $($r2.Content)"
