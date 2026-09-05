const crypto = require('crypto');

async function fireWebhook(amount, id) {
    const payload = {
        event: "checkout.abandoned",
        payload: {
            payment: {
                entity: {
                    id: id,
                    amount: amount,
                    currency: "INR",
                    status: "failed",
                    error_code: "customer_cancelled",
                    created_at: Math.floor(Date.now() / 1000)
                }
            }
        }
    };

    const payloadStr = JSON.stringify(payload);
    const secret = "hwk_test_secret_123";
    const signature = crypto.createHmac('sha256', secret).update(payloadStr).digest('hex');

    const res = await fetch('http://localhost:8080/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Razorpay-Signature': signature
        },
        body: payloadStr
    });

    console.log(`Fired ${amount}, response: ${res.status}`);
}

async function run() {
    await fireWebhook(500000, "cart_test_5000"); // 5000 INR
    await fireWebhook(50000, "cart_test_500"); // 500 INR
}

run();
