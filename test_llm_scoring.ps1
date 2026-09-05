$SECRET = "hwk_test_secret_123"
$URL_WEBHOOK = "http://localhost:8080/webhook"

function FireWebhook {
    param([string]$eventId, [string]$paymentId, [string]$errorCode)

    $TIMESTAMP = [int][double]::Parse((Get-Date (Get-Date).ToUniversalTime() -UFormat %s))
    $PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"' + $paymentId + '","amount":100000,"currency":"INR","status":"failed","error_code":"' + $errorCode + '","created_at":' + $TIMESTAMP + '}}}}'

    $hmac = new-object System.Security.Cryptography.HMACSHA256
    $hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
    $hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
    $VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

    Write-Host "Firing webhook for $paymentId with $errorCode..."
    Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"=$eventId} -UseBasicParsing | Out-Null
}

# 1. Soft failure
FireWebhook -eventId "evt_llm_001" -paymentId "pay_llm_001" -errorCode "insufficient_funds"

Start-Sleep -Seconds 2

# 2. Hard failure
FireWebhook -eventId "evt_llm_002" -paymentId "pay_llm_002" -errorCode "suspected_fraud"

Write-Host "Check backend logs!"
