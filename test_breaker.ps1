$SECRET = "hwk_test_secret_123"
$URL_WEBHOOK = "http://localhost:8080/webhook"
$TIMESTAMP = [int][double]::Parse((Get-Date (Get-Date).ToUniversalTime() -UFormat %s))

$PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"pay_brk_001","amount":75000,"currency":"INR","status":"failed","error_code":"unknown","created_at":' + $TIMESTAMP + '}}}}'

$hmac = new-object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
$hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
$VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

Write-Host "Firing 4 consecutive webhooks to trigger breaker..."
for ($i=1; $i -le 4; $i++) {
    $EVENT_ID = "evt_brk_00" + $i
    Write-Host "`nAttempt $i..."
    $r = Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"=$EVENT_ID} -UseBasicParsing
    Write-Host "Response: $($r.Content)"
    Start-Sleep -Seconds 1
}
