import re

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

dashboard_ui = r"""          </div>
        </div>

      {/* BATCH DASHBOARD */}
      <div className="col-span-12 mb-2">
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

# Replace the closing div of the HEADER with the closing div + the new dashboard
c = c.replace('          </div>\n        </div>', dashboard_ui, 1)

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
