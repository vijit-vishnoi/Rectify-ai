import urllib.request
import json
import time
import hmac
import hashlib

SECRET = b'hwk_test_secret_123'
BASE_URL = 'http://localhost:8080'

def send_webhook(event_id, payment_id, event_type, amount, trai=False, ff24=False, promise_date=None):
    payload = {
        "event": event_type,
        "trai_quiet_hours": trai,
        "fast_forward_24h": ff24,
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": amount,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "insufficient_funds",
                    "created_at": int(time.time())
                }
            }
        }
    }
    if promise_date:
        payload["payload"]["payment"]["entity"]["promise_date"] = promise_date

    body = json.dumps(payload).encode('utf-8')
    signature = hmac.new(SECRET, body, hashlib.sha256).hexdigest()

    req = urllib.request.Request(f"{BASE_URL}/webhook", data=body, headers={
        'Content-Type': 'application/json',
        'X-Razorpay-Event-Id': event_id,
        'X-Razorpay-Signature': signature
    }, method='POST')
    
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        return e.code
    return 200

def get_ledger(payment_id):
    req = urllib.request.Request(f"{BASE_URL}/ledger")
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    return [d for d in data if d.get('event_id') == payment_id]

def wait_for_ledger(payment_id, expected_length, max_retries=10):
    for _ in range(max_retries):
        l = get_ledger(payment_id)
        if len(l) >= expected_length:
            return l
        time.sleep(0.5)
    return get_ledger(payment_id)

print("Starting Verification Suite...\n")
results = []

def record_result(flow, passed, action, ev, details=""):
    status = "PASS" if passed else "FAIL"
    results.append(f"[{status}] Flow {flow}: Action={action} | EV={ev} | {details}")

# Flow A
try:
    send_webhook("evt_a1", "pay_flow_a", "payment.failed", 100000, False, False)
    l1 = wait_for_ledger("pay_flow_a", 1)
    act1 = l1[-1]['action_taken']
    ev1 = l1[-1]['expected_value']
    pass_a1 = act1 == "SEND_PRE_DEBIT_NOTICE"
    
    send_webhook("evt_a2", "pay_flow_a", "payment.failed", 100000, False, True)
    l2 = wait_for_ledger("pay_flow_a", 2)
    act2 = l2[-1]['action_taken']
    ev2 = l2[-1]['expected_value']
    pass_a2 = act2 in ["RETRY_SAME_RAIL", "RETRY_ALT_RAIL"]
    
    record_result("A (RBI & Notice Cooldown)", pass_a1 and pass_a2, f"{act1} -> {act2}", f"{ev1} -> {ev2}")
except Exception as e:
    record_result("A (RBI & Notice Cooldown)", False, "ERROR", 0, str(e))

# Flow B
try:
    send_webhook("evt_b1", "pay_flow_b", "payment.failed", 100000, True, False)
    l = wait_for_ledger("pay_flow_b", 1)
    act = l[-1]['action_taken']
    ev = l[-1]['expected_value']
    record_result("B (TRAI Quiet Hours)", act == "STOP", act, ev)
except Exception as e:
    record_result("B (TRAI Quiet Hours)", False, "ERROR", 0, str(e))

# Flow C
try:
    send_webhook("evt_c1", "pay_flow_c", "checkout.abandoned", 500000, False, False)
    l = wait_for_ledger("pay_flow_c", 1)
    act = l[-1]['action_taken']
    ev = l[-1]['expected_value']
    record_result("C (Drop-off Discount Math)", "SEND_DISCOUNT" in act, act, ev)
except Exception as e:
    record_result("C (Drop-off Discount Math)", False, "ERROR", 0, str(e))

# Flow D
try:
    send_webhook("evt_d1", "pay_flow_d", "promise_to_pay", 100000, False, False, int(time.time()) + 86400)
    l1 = wait_for_ledger("pay_flow_d", 1)
    act1 = l1[-1]['action_taken']
    
    send_webhook("evt_d2", "pay_flow_d", "payment.failed", 100000, False, False)
    l2 = wait_for_ledger("pay_flow_d", 2)
    act2 = l2[-1]['action_taken']
    
    record_result("D (Promise-to-Pay Trap)", act1 == "PROMISE_LOGGED" and act2 == "PROMISE_PENDING", f"{act1} -> {act2}", f"{l1[-1]['expected_value']} -> {l2[-1]['expected_value']}")
except Exception as e:
    record_result("D (Promise-to-Pay Trap)", False, "ERROR", 0, str(e))

# Flow E
try:
    req = urllib.request.Request(f"{BASE_URL}/tts?text=hello")
    res = urllib.request.urlopen(req)
    ctype = res.headers.get('Content-Type', '')
    passed = res.status == 200 and 'audio/mpeg' in ctype
    record_result("E (TTS Proxy)", passed, f"HTTP {res.status}", len(res.read()), ctype)
except Exception as e:
    record_result("E (TTS Proxy)", False, "ERROR", 0, str(e))

# Flow F
try:
    send_webhook("evt_f1", "pay_flow_f", "payment.failed", 100000, False, False)
    l1 = wait_for_ledger("pay_flow_f", 1)
    
    send_webhook("evt_f1", "pay_flow_f", "payment.failed", 100000, False, False)
    time.sleep(2)
    l2 = get_ledger("pay_flow_f")
    
    # either it blocks it (length 1) or hits notice cooldown (second action is STOP/WAIT)
    passed = len(l2) == 1 or l2[-1]['action_taken'] in ["STOP", "WAIT"]
    act = "BLOCKED" if len(l2) == 1 else l2[-1]['action_taken']
    ev = 0 if len(l2) == 1 else l2[-1]['expected_value']
    record_result("F (Dispatch Idempotency)", passed, act, ev)
except Exception as e:
    record_result("F (Dispatch Idempotency)", False, "ERROR", 0, str(e))

# Flow G
try:
    send_webhook("evt_g1", "pay_flow_g", "order.paid", 100000, False, False)
    # wait for state to update
    time.sleep(1)
    
    send_webhook("evt_g2", "pay_flow_g", "payment.failed", 100000, False, False)
    l = wait_for_ledger("pay_flow_g", 1)
    act = l[-1]['action_taken']
    ev = l[-1]['expected_value']
    
    record_result("G (Settlement Abortion)", act == "STOP", act, ev)
except Exception as e:
    record_result("G (Settlement Abortion)", False, "ERROR", 0, str(e))

# Flow H
try:
    send_webhook("evt_h1", "pay_flow_h", "payment.failed", 100000, False, False)
    wait_for_ledger("pay_flow_h", 1)
    
    actions = []
    for i in range(5):
        send_webhook(f"evt_h{i+2}", "pay_flow_h", "payment.failed", 100000, False, True)
        time.sleep(1)
    
    l = get_ledger("pay_flow_h")
    for rec in l:
        actions.append(rec['action_taken'])
    
    passed = "STOP" in actions
    record_result("H (Max Attempt Caps)", passed, actions[-1], l[-1]['expected_value'], f"Total Actions: {len(actions)}")
except Exception as e:
    record_result("H (Max Attempt Caps)", False, "ERROR", 0, str(e))

print("\n".join(results))
