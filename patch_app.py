with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "r", encoding="utf-8") as f:
    c = f.read()

old_run = """  const runBatch = async () => {
    setBatchRunning(true);
    try {
      await fetch('/batch/simulate', { method: 'POST' });
    } catch(err) {}
    setBatchRunning(false);
  };"""

new_run = """  const runBatch = async () => {
    setBatchRunning(true);
    try {
      await fetch('/batch/simulate', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 1000 })
      });
    } catch(err) {}
    setBatchRunning(false);
  };"""

c = c.replace(old_run, new_run)

old_form = """            <form onSubmit={simulateWebhook} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Amount (INR)</label>"""

new_form = """            <form onSubmit={simulateWebhook} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Payment ID</label>
                <input type="text" value={paymentId} onChange={(e) => setPaymentId(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-blue-500 transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Amount (INR)</label>"""

c = c.replace(old_form, new_form)

with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as f:
    f.write(c)
