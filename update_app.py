import re
with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add states for metrics
state_replacement = """  const [traiQuietHours, setTraiQuietHours] = useState(false);
  const [fastForward24h, setFastForward24h] = useState(false);

  const [metrics, setMetrics] = useState({ total_at_risk: 0, total_recovered: 0, total_cost: 0 });
  const [batchRunning, setBatchRunning] = useState(false);"""

c = c.replace('  const [fastForward24h, setFastForward24h] = useState(false);', state_replacement)

# Add fetchMetrics
fetch_metrics = """    const verifyChain = async () => {
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
    };"""

c = c.replace('    const verifyChain = async () => {\n      try {\n        const res = await fetch(\'/ledger/verify\');\n        const data = await res.json();\n        console.log("[DIAGNOSTIC] Incoming Payload:", data);\n        setChainValid(data.valid);\n        setBlocksChecked(data.blocks_checked);\n      } catch (err) {}\n    };', fetch_metrics)

# Add polling
poll_replacement = """    const ledgerInterval = setInterval(fetchLedger, 2000);
    const verifyInterval = setInterval(verifyChain, 2500);
    const metricsInterval = setInterval(fetchMetrics, 1000);

    fetchLedger();
    verifyChain();
    fetchMetrics();

    return () => {
      clearInterval(ledgerInterval);
      clearInterval(verifyInterval);
      clearInterval(metricsInterval);
    };"""

c = re.sub(r'    const ledgerInterval = setInterval\(fetchLedger, 2000\);.*?clearInterval\(verifyInterval\);\n    };\n', poll_replacement, c, flags=re.DOTALL)

# Add runBatch function
run_batch = """  const runBatch = async () => {
    setBatchRunning(true);
    await fetch('/batch/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count: 1000 })
    });
    setTimeout(() => setBatchRunning(false), 3000);
  };

  const getBasePayload"""

c = c.replace('  const getBasePayload', run_batch)

# Add the dashboard UI below the header
header_regex = r'(<header.*?</header>)'
dashboard_ui = r"""\1

      {/* BATCH DASHBOARD */}
      <div className="col-span-12 mb-6">
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-lg p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" />
                Live Batch Execution Metrics
              </h2>
              <p className="text-xs text-zinc-400 mt-1">Real-time telemetry of autonomous revenue recovery operations.</p>
            </div>
            <button onClick={runBatch} disabled={batchRunning} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 px-6 rounded-md transition-colors text-sm flex items-center gap-2">
              {batchRunning ? <Activity className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {batchRunning ? 'Simulating...' : 'Run 1,000x Batch'}
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
              <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">Total At Risk</p>
              <p className="text-2xl font-bold text-red-400">?{(metrics.total_at_risk / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
              <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">AI Recovered</p>
              <p className="text-2xl font-bold text-green-400">?{(metrics.total_recovered / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
              <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">Intervention Cost</p>
              <p className="text-2xl font-bold text-orange-400">?{(metrics.total_cost / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
              <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">Net ROI</p>
              <p className="text-2xl font-bold text-blue-400">
                {metrics.total_cost > 0 ? (((metrics.total_recovered - metrics.total_cost) / metrics.total_cost) * 100).toFixed(0) : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>"""

c = re.sub(header_regex, dashboard_ui, c, flags=re.DOTALL)

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
