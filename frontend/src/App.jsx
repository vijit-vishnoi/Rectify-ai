import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, ShieldAlert, Send, Bot, Play, Volume2 } from 'lucide-react';

export default function App() {
  const [ledger, setLedger] = useState([]);
  const [chainValid, setChainValid] = useState(true);
  const [blocksChecked, setBlocksChecked] = useState(0);

  const [paymentId, setPaymentId] = useState('pay_' + Math.random().toString(36).substr(2, 6));
    const [eventType, setEventType] = useState('payment.failed');
  const [amount, setAmount] = useState('1000');
  const [errorCode, setErrorCode] = useState('insufficient_funds');
  const [traiQuietHours, setTraiQuietHours] = useState(false);
  const [fastForward24h, setFastForward24h] = useState(false);

  const [metrics, setMetrics] = useState({ total_at_risk: 0, total_recovered: 0, total_cost: 0 });
  const [batchRunning, setBatchRunning] = useState(false);

  const [voiceCallActive, setVoiceCallActive] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [lastVoiceSeq, setLastVoiceSeq] = useState(-1);

  const playVoice = (text) => {
    console.log("[AUDIO] playVoice called with text:", text);
    if (!text) return;
    
    try {
      console.log("[AUDIO] window.speechSynthesis is structurally blocked. Pivoting to HTML5 Audio fallback.");
      
      // Pivot to standard HTML5 audio using a public TTS endpoint as fallback
      // Splitting text if it's too long, but for 2 sentences it fits within typical URL limits (200 chars for tw-ob).
      // Since it might exceed 200 chars, we can just use the first 200 chars or split by sentence.
      let safeText = text.length > 200 ? text.substring(0, 197) + "..." : text;
      const url = `http://localhost:8080/tts?text=${encodeURIComponent(text)}`;
      
      const audio = new Audio(url);
      audio.onplay = () => console.log("[AUDIO] HTML5 Audio started playing");
      audio.onerror = (e) => console.error("[AUDIO] HTML5 Audio network/404 error code:", audio.error ? audio.error.code : "unknown", audio.error ? audio.error.message : "");
      audio.onended = () => console.log("[AUDIO] HTML5 Audio finished");
      audio.play().catch(err => console.log("[AUDIO] Autoplay prevented, waiting for user click:", err));
      
    } catch (err) {
      console.log("[AUDIO] Fallback error:", err);
    }
  };

  useEffect(() => {
    if (ledger.length > 0) {
      const latest = ledger[0];
      if (latest.action_taken === 'ESCALATE_VOICE_HINGLISH' && latest.seq > lastVoiceSeq && !latest.event_id.includes('batch')) {
        setLastVoiceSeq(latest.seq);
        setVoiceTranscript(latest.voice_script || "");
        setVoiceCallActive(true);
        playVoice(latest.voice_script || "");
      }
    }
  }, [ledger, lastVoiceSeq]);


  useEffect(() => {
    const fetchLedger = async () => {
      try {
        const res = await fetch('/ledger');
        const data = await res.json();
        setLedger(data.reverse()); 
      } catch (err) {}
    };

    const verifyChain = async () => {
      try {
        const res = await fetch('/ledger/verify');
        const data = await res.json();
        setChainValid(data.valid);
        setBlocksChecked(data.blocks_checked);
      } catch (err) {}
    };

    const fetchMetrics = async () => {
      try {
        const res = await fetch('/metrics');
        const data = await res.json();
        setMetrics(data);
      } catch (err) {}
    };

    const ledgerInterval = setInterval(fetchLedger, 2000);
    const verifyInterval = setInterval(verifyChain, 2500);
    const metricsInterval = setInterval(fetchMetrics, 1000);

    fetchLedger();
    verifyChain();
    fetchMetrics();

    return () => {
      clearInterval(ledgerInterval);
      clearInterval(verifyInterval);
      clearInterval(metricsInterval);
    };
  }, []);

  const sendWebhook = async (payload, eventId = "") => {
    const secret = "hwk_test_secret_123";
    const payloadStr = JSON.stringify(payload);
    
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const key = await crypto.subtle.importKey(
      'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
    );
    const signatureBuffer = await crypto.subtle.sign('HMAC', key, encoder.encode(payloadStr));
    const signatureArray = Array.from(new Uint8Array(signatureBuffer));
    const signatureHex = signatureArray.map(b => b.toString(16).padStart(2, '0')).join('');

    const headers = {
      'Content-Type': 'application/json',
      'X-Razorpay-Signature': signatureHex
    };
    if (eventId) headers['X-Razorpay-Event-Id'] = eventId;

    await fetch('/webhook', { method: 'POST', headers, body: payloadStr });
    setTimeout(async () => {
      try {
        const res = await fetch('/ledger');
        const data = await res.json();
        setLedger(data.reverse()); 
      } catch (err) {}
    }, 500);
  };

  const simulateWebhook = (e) => {
    e.preventDefault();
    const now = new Date();
    if (fastForward24h) now.setHours(now.getHours() + 25);

    const payload = {
      event: eventType,
        trai_quiet_hours: traiQuietHours,
        fast_forward_24h: fastForward24h,
        payload: {
        payment: {
          entity: {
            id: paymentId,
            amount: parseInt(amount, 10) * 100,
            currency: "INR",
            status: "failed",
            error_code: errorCode,
            created_at: Math.floor(now.getTime() / 1000)
          }
        }
      }
    };
    sendWebhook(payload);
  };

  const testDuplicateIdempotency = () => {
    const id = 'pay_dup_' + Math.random().toString(36).substr(2, 6);
    const payload = {
      event: eventType,
        trai_quiet_hours: traiQuietHours,
        fast_forward_24h: fastForward24h,
        payload: { payment: { entity: { id: id, amount: 50000, currency: "INR", status: "failed", error_code: "insufficient_funds", created_at: Math.floor(Date.now() / 1000) } } }
    };
    const eventId = "evt_" + Math.random().toString(36).substr(2, 6);
    sendWebhook(payload, eventId);
    setTimeout(() => sendWebhook(payload, eventId), 1000);
  };

  const testSettlementGuard = async () => {
    const id = 'pay_set_' + Math.random().toString(36).substr(2, 6);
    await fetch('/admin/order/pay', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ payment_id: id })
    });
    const payload = {
      event: eventType,
        trai_quiet_hours: traiQuietHours,
        fast_forward_24h: fastForward24h,
        payload: { payment: { entity: { id: id, amount: 20000, currency: "INR", status: "failed", error_code: "insufficient_funds", created_at: Math.floor(Date.now() / 1000) } } }
    };
    sendWebhook(payload);
  };

  const testPromiseToPay = async () => {
    const payload = {
      event: "promise_to_pay",
      trai_quiet_hours: traiQuietHours,
      fast_forward_24h: fastForward24h,
      payload: { payment: { entity: { id: paymentId, promise_date: Math.floor(Date.now() / 1000) + (5 * 24 * 60 * 60) } } }
    };
    sendWebhook(payload);
  };

  const testAgeLimit = () => {
    const id = 'pay_age_' + Math.random().toString(36).substr(2, 6);
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 30);
    const payload = {
      event: eventType,
        trai_quiet_hours: traiQuietHours,
        fast_forward_24h: fastForward24h,
        payload: { payment: { entity: { id: id, amount: 50000, currency: "INR", status: "failed", error_code: "insufficient_funds", created_at: Math.floor(oldDate.getTime() / 1000) } } }
    };
    sendWebhook(payload);
  };

  const runBatch = async () => {
    setBatchRunning(true);
    try {
      await fetch('/batch/simulate', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 1000 })
      });
    } catch(err) {}
    setBatchRunning(false);
  };

  const getBadgeColor = (action) => {
    switch(action) {
      case 'STOP': return 'bg-red-950 text-red-400 border-red-900';
      case 'WAIT': return 'bg-zinc-800 text-zinc-400 border-zinc-700';
      case 'SEND_PRE_DEBIT_NOTICE': return 'bg-purple-950 text-purple-400 border-purple-900';
      case 'RETRY_ALT_RAIL': return 'bg-indigo-950 text-indigo-400 border-indigo-900';
      case 'DISPATCH_VOICE_AGENT': return 'bg-green-950 text-green-400 border-green-900';
      case 'ESCALATE_HUMAN': return 'bg-orange-950 text-orange-400 border-orange-900';
      case 'ESCALATE_VOICE_HINGLISH': return 'bg-emerald-950 text-emerald-400 border-emerald-900';
      case 'SEND_DISCOUNT_5': return 'bg-pink-950 text-pink-400 border-pink-900';
      case 'SEND_DISCOUNT_10': return 'bg-rose-950 text-rose-400 border-rose-900';
      default: return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-200 p-6 font-sans">
      <div className="mb-8 flex items-center justify-between border-b border-zinc-800/80 pb-6 max-w-[1600px] mx-auto w-full">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-500" />
            Rectify-AI Core
          </h1>
          <p className="text-zinc-500 text-sm mt-1">Autonomous Revenue Recovery Engine</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-zinc-900 border border-zinc-800/80 rounded px-4 py-2 flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${chainValid ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Ledger State</p>
              <p className="text-xs font-medium">{chainValid ? 'VERIFIED' : 'TAMPERED'}</p>
            </div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800/80 rounded px-4 py-2 flex items-center gap-3">
            <Activity className="w-4 h-4 text-zinc-500" />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Blocks Secured</p>
              <p className="text-xs font-mono">{blocksChecked}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 items-start max-w-[1600px] mx-auto w-full">
        {/* SIMULATOR */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <div className="bg-zinc-900 border border-zinc-800/80 rounded-lg p-5 shadow-sm">
            <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-5">Webhook Simulator</h2>
            <form onSubmit={simulateWebhook} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Payment ID</label>
                <input type="text" value={paymentId} onChange={(e) => setPaymentId(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-blue-500 transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Amount (INR)</label>
                <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-blue-500 transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Event Type</label>
                <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-blue-500 transition-colors mb-4">
                  <option value="payment.failed">payment.failed (Degradation)</option>
                  <option value="checkout.abandoned">checkout.abandoned (Drop-off)</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Error Code</label>
                <select value={errorCode} onChange={(e) => setErrorCode(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-blue-500 transition-colors">
                  <option value="insufficient_funds">insufficient_funds</option>
                  <option value="network_error">network_error</option>
                  <option value="invalid_card">invalid_card</option>
                  <option value="customer_cancelled">customer_cancelled</option>
                </select>
              </div>
              <div className="pt-2 flex flex-col gap-2">
                <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                  <input type="checkbox" checked={traiQuietHours} onChange={(e) => setTraiQuietHours(e.target.checked)} className="rounded border-zinc-800 bg-zinc-950" />
                  Simulate TRAI Quiet Hours
                </label>
                <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                  <input type="checkbox" checked={fastForward24h} onChange={(e) => setFastForward24h(e.target.checked)} className="rounded border-zinc-800 bg-zinc-950" />
                  Fast-Forward 24h (Bypass RBI)
                </label>
              </div>
              <button type="submit" className="w-full bg-white hover:bg-zinc-200 text-zinc-900 font-semibold py-2 px-4 rounded transition-colors text-sm flex items-center justify-center gap-2 mt-4">
                <Send className="w-4 h-4" />
                Simulate Webhook
              </button>
            </form>
          </div>

          <div className="bg-zinc-900 border border-zinc-800/80 rounded-lg p-5 shadow-sm">
            <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              Test Guardrails
            </h2>
            <div className="space-y-2 flex flex-col">
              <button onClick={testDuplicateIdempotency} className="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 py-2 px-3 rounded transition-colors text-left flex items-center justify-between">
                <span>Test Idempotency</span>
                <span className="text-[10px] text-zinc-500">Duplicate Event</span>
              </button>
              <button onClick={testSettlementGuard} className="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 py-2 px-3 rounded transition-colors text-left flex items-center justify-between">
                <span>Test Settlement Guard</span>
                <span className="text-[10px] text-zinc-500">order.paid ? failed</span>
              </button>
              <button onClick={testPromiseToPay} className="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 py-2 px-3 rounded transition-colors text-left flex items-center justify-between">
                <span>Test Promise-to-Pay</span>
                <span className="text-[10px] text-zinc-500">POST /promise ? failed</span>
              </button>
              <button onClick={testAgeLimit} className="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 py-2 px-3 rounded transition-colors text-left flex items-center justify-between">
                <span>Test 21-Day Age Limit</span>
                <span className="text-[10px] text-zinc-500">30 days ago</span>
              </button>
            </div>
          </div>
        </div>
  
        {/* RIGHT COLUMN: BATCH DASHBOARD + LEDGER */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-6 h-[calc(100vh-80px)]">
          {/* BATCH DASHBOARD */}
          <div className="w-full shrink-0 animated-border-wrapper">
            <div className="glass-panel rounded-lg p-6 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-transparent to-purple-900/10 z-[-1]" />
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-400" />
                    Live Batch Execution Metrics
                  </h2>
                  <p className="text-xs text-zinc-400 mt-1">Real-time telemetry of autonomous revenue recovery operations.</p>
                </div>
                <button onClick={runBatch} disabled={batchRunning} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-[0_0_15px_rgba(79,70,229,0.4)] disabled:shadow-none disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2.5 px-6 rounded-lg transition-all text-sm flex items-center gap-2 border border-blue-500/30">
                  {batchRunning ? <Activity className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {batchRunning ? 'Simulating...' : 'Run 1,000x Batch'}
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                <div className="bg-zinc-950/80 border border-red-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(248,113,113,0.05)] hover:shadow-[0_0_20px_rgba(248,113,113,0.1)] transition-all">
                  <p className="text-[11px] text-red-500/70 uppercase tracking-widest font-bold mb-2">Total At Risk</p>
                  <p className="text-3xl font-black text-red-400 tracking-tight drop-shadow-[0_0_8px_rgba(248,113,113,0.4)]">₹ {(metrics.total_at_risk / 100).toLocaleString()}</p>
                </div>
                <div className="bg-zinc-950/80 border border-emerald-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(52,211,153,0.05)] hover:shadow-[0_0_20px_rgba(52,211,153,0.1)] transition-all">
                  <p className="text-[11px] text-emerald-500/70 uppercase tracking-widest font-bold mb-2">AI Recovered</p>
                  <p className="text-3xl font-black text-emerald-400 tracking-tight drop-shadow-[0_0_8px_rgba(52,211,153,0.4)]">₹ {(metrics.total_recovered / 100).toLocaleString()}</p>
                </div>
                <div className="bg-zinc-950/80 border border-orange-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(251,146,60,0.05)] hover:shadow-[0_0_20px_rgba(251,146,60,0.1)] transition-all">
                  <p className="text-[11px] text-orange-500/70 uppercase tracking-widest font-bold mb-2">Intervention Cost</p>
                  <p className="text-3xl font-black text-orange-400 tracking-tight drop-shadow-[0_0_8px_rgba(251,146,60,0.4)]">₹ {(metrics.total_cost / 100).toLocaleString()}</p>
                </div>
                <div className="bg-zinc-950/80 border border-blue-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(96,165,250,0.05)] hover:shadow-[0_0_20px_rgba(96,165,250,0.1)] transition-all relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/10 blur-xl rounded-full" />
                  <p className="text-[11px] text-blue-500/70 uppercase tracking-widest font-bold mb-2">Net ROI</p>
                  <p className="text-3xl font-black text-blue-400 tracking-tight drop-shadow-[0_0_8px_rgba(96,165,250,0.4)] relative z-10">
                    {metrics.total_cost > 0 ? (((metrics.total_recovered - metrics.total_cost) / metrics.total_cost) * 100).toLocaleString() : 0}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* LEDGER */}
          <div className="glass-panel rounded-xl shadow-xl flex flex-col flex-1 min-h-0 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-zinc-800 via-blue-500/50 to-zinc-800 opacity-30"></div>
            <div className="px-6 py-5 border-b border-zinc-800/60 bg-zinc-900/40 shrink-0">
              <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                Immutable Operations Ledger
              </h2>
            </div>
            <div className="overflow-auto flex-1 custom-scrollbar">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="text-zinc-400 font-semibold sticky top-0 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/80 z-10 shadow-sm">
                  <tr>
                    <th className="py-3 px-5 font-medium">Seq</th>
                    <th className="py-3 px-5 font-medium">Timestamp</th>
                    <th className="py-3 px-5 font-medium">Payment ID</th>
                    <th className="py-3 px-5 font-medium">Attempts</th>
                    <th className="py-3 px-5 font-medium">Action Taken</th>
                    <th className="py-3 px-5 font-medium text-right">Expected Value</th>
                    <th className="py-3 px-5 font-medium text-right">P(Recover)</th>
                    <th className="py-3 px-5 font-medium text-right">Block Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {ledger.map((record) => (
                    <tr key={record.seq} className="hover:bg-zinc-800/40 transition-colors duration-200 group border-l-[3px] border-transparent hover:border-blue-500/50">
                      <td className="py-3 px-5 text-zinc-500 font-mono">#{String(record.seq).padStart(4, '0')}</td>
                      <td className="py-3 px-5 text-zinc-400">{new Date(record.timestamp).toLocaleTimeString([], {hour12: false})}</td>
                      <td className="py-3 px-5 font-mono text-zinc-300">{record.event_id}</td>
                      <td className="py-3 px-5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${record.attempt_count === 0 ? 'bg-blue-900/50 text-blue-300 border-blue-500/30' : 'bg-zinc-800/50 text-zinc-400 border-zinc-700/50'}`}>
                          {record.attempt_count}
                        </span>
                      </td>
                      <td className="py-3 px-5">
                        <div className="flex flex-col gap-1.5 items-start">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border tracking-wider ${getBadgeColor(record.action_taken)}`}>
                            {record.action_taken.replace(/_/g, ' ')}
                          </span>
                          {record.llm_reasoning && (
                            <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 bg-zinc-950/50 px-1.5 py-0.5 rounded border border-zinc-800/80 max-w-[220px]" title={record.llm_reasoning}>
                              <Bot className="w-3 h-3 text-zinc-500 shrink-0" />
                              <span className="truncate">{record.llm_reasoning}</span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-5 text-right font-medium text-zinc-200">
                        INR {(record.expected_value / 100).toFixed(2)}
                      </td>
                      <td className="py-3 px-5 text-right font-medium text-zinc-400">
                        {(record.p_recover * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-5 text-right">
                        <span className="font-mono text-[10px] text-zinc-500 bg-zinc-950/50 px-1.5 py-1 rounded cursor-help border border-zinc-800/80 transition-colors group-hover:border-zinc-700" title={`Full Hash: ${record.hash}\nPrev Hash: ${record.previous_hash}`}>
                          {record.hash.substring(0, 12)}...
                        </span>
                      </td>
                    </tr>
                  ))}
                  {ledger.length === 0 && (
                    <tr>
                      <td colSpan="7" className="py-12 text-center text-zinc-600 text-sm">No events processed yet. Simulate a webhook to begin.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      {voiceCallActive && (
        <div className="fixed bottom-6 right-6 w-80 bg-zinc-900 border border-emerald-500/50 rounded-xl shadow-2xl p-4 overflow-hidden shadow-[0_0_15px_rgba(16,185,129,0.2)]">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-950 flex items-center justify-center">
                <Volume2 className="w-4 h-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Rectify AI Voice Bot</p>
                <p className="text-[10px] text-emerald-500 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live Call
                </p>
              </div>
            </div>
            <button onClick={() => setVoiceCallActive(false)} className="text-zinc-500 hover:text-zinc-300 text-xs">Close</button>
          </div>
          <div className="bg-black/50 rounded p-3 text-sm text-zinc-300 font-mono mb-3 h-24 overflow-y-auto">
            {voiceTranscript}
          </div>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-1">
              <div className="w-1 h-3 bg-emerald-500 animate-[pulse_1s_infinite]" />
              <div className="w-1 h-4 bg-emerald-500 animate-[pulse_1.2s_infinite]" />
              <div className="w-1 h-2 bg-emerald-500 animate-[pulse_0.8s_infinite]" />
              <div className="w-1 h-5 bg-emerald-500 animate-[pulse_1.5s_infinite]" />
            </div>
            <button onClick={() => playVoice(voiceTranscript)} className="flex items-center gap-1 px-3 py-1 bg-emerald-950 text-emerald-400 hover:bg-emerald-900 rounded text-xs transition-colors">
              <Play className="w-3 h-3" /> Replay
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

