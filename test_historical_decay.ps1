$SECRET = "hwk_test_secret_123"
$URL_WEBHOOK = "http://localhost:8080/webhook"
$PAYMENT_ID = "pay_hist_001"

function FireWebhook {
    param([string]$eventId)

    $TIMESTAMP = [int][double]::Parse((Get-Date (Get-Date).ToUniversalTime() -UFormat %s))
    $PAYLOAD = '{"event":"payment.failed","account_id":"acc_123","payload":{"payment":{"entity":{"id":"' + $PAYMENT_ID + '","amount":100000,"currency":"INR","status":"failed","error_code":"insufficient_funds","created_at":' + $TIMESTAMP + '}}}}'

    $hmac = new-object System.Security.Cryptography.HMACSHA256
    $hmac.Key = [Text.Encoding]::UTF8.GetBytes($SECRET)
    $hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($PAYLOAD))
    $VALID_SIG = [BitConverter]::ToString($hash).Replace('-', '').ToLower()

    Write-Host "Firing webhook for $PAYMENT_ID (Event: $eventId)..."
    Invoke-WebRequest -Uri $URL_WEBHOOK -Method Post -Body $PAYLOAD -ContentType "application/json" -Headers @{"X-Razorpay-Signature"=$VALID_SIG; "x-razorpay-event-id"=$eventId} -UseBasicParsing | Out-Null
}

FireWebhook "evt_hist_1"
Start-Sleep -Seconds 1
FireWebhook "evt_hist_2"
Start-Sleep -Seconds 1
FireWebhook "evt_hist_3"
Start-Sleep -Seconds 1
FireWebhook "evt_hist_4"

Write-Host "Check backend logs!"
