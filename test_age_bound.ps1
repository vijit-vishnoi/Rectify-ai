$SECRET = "hwk_test_secret_123"
$URL_WEBHOOK = "http://localhost:8080/webhook"

$OLD_TIMESTAMP = [int][double]::Parse((Get-Date).AddDays(-30).ToUniversalTime().Subtract([datetime]'1970-01-01').TotalSeconds)

$PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_aged_001","amount":75000,"currency":"INR","status":"failed","error_code":"insufficient_funds","created_at":' + $OLD_TIMESTAMP + '}}}}'

$hmac = new-object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
$hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
$VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

Write-Host "Firing webhook for aged receivable (pay_aged_001)..."
$r = Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"="evt_aged_001"} -UseBasicParsing
Write-Host "Response: $($r.Content)"
