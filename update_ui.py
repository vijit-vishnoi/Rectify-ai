import re

with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "r", encoding="utf-8") as f:
    c = f.read()

# Make the batch dashboard "matrix" look ultra-premium
old_batch = """      {/* BATCH DASHBOARD */}
      <div className="col-span-12 mb-2">
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-lg p-5 shadow-sm">"""

new_batch = """      {/* BATCH DASHBOARD */}
      <div className="col-span-12 mb-4 animated-border-wrapper">
        <div className="glass-panel rounded-lg p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-transparent to-purple-900/10 z-[-1]" />"""
          
c = c.replace(old_batch, new_batch)

# Metrics Cards
old_metrics = """          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
          </div>"""

new_metrics = """          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <div className="bg-zinc-950/80 border border-red-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(248,113,113,0.05)] hover:shadow-[0_0_20px_rgba(248,113,113,0.1)] transition-all">
              <p className="text-[11px] text-red-500/70 uppercase tracking-widest font-bold mb-2">Total At Risk</p>
              <p className="text-3xl font-black text-red-400 tracking-tight drop-shadow-[0_0_8px_rgba(248,113,113,0.4)]">?{(metrics.total_at_risk / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950/80 border border-emerald-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(52,211,153,0.05)] hover:shadow-[0_0_20px_rgba(52,211,153,0.1)] transition-all">
              <p className="text-[11px] text-emerald-500/70 uppercase tracking-widest font-bold mb-2">AI Recovered</p>
              <p className="text-3xl font-black text-emerald-400 tracking-tight drop-shadow-[0_0_8px_rgba(52,211,153,0.4)]">?{(metrics.total_recovered / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950/80 border border-orange-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(251,146,60,0.05)] hover:shadow-[0_0_20px_rgba(251,146,60,0.1)] transition-all">
              <p className="text-[11px] text-orange-500/70 uppercase tracking-widest font-bold mb-2">Intervention Cost</p>
              <p className="text-3xl font-black text-orange-400 tracking-tight drop-shadow-[0_0_8px_rgba(251,146,60,0.4)]">?{(metrics.total_cost / 100).toLocaleString()}</p>
            </div>
            <div className="bg-zinc-950/80 border border-blue-900/30 rounded-xl p-5 shadow-[0_0_15px_rgba(96,165,250,0.05)] hover:shadow-[0_0_20px_rgba(96,165,250,0.1)] transition-all relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/10 blur-xl rounded-full" />
              <p className="text-[11px] text-blue-500/70 uppercase tracking-widest font-bold mb-2">Net ROI</p>
              <p className="text-3xl font-black text-blue-400 tracking-tight drop-shadow-[0_0_8px_rgba(96,165,250,0.4)] relative z-10">
                {metrics.total_cost > 0 ? (((metrics.total_recovered - metrics.total_cost) / metrics.total_cost) * 100).toLocaleString() : 0}%
              </p>
            </div>
          </div>"""

c = c.replace(old_metrics, new_metrics)

# Button styling
old_btn = """<button onClick={runBatch} disabled={batchRunning} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 px-6 rounded-md transition-colors text-sm flex items-center gap-2">"""
new_btn = """<button onClick={runBatch} disabled={batchRunning} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-[0_0_15px_rgba(79,70,229,0.4)] disabled:shadow-none disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2.5 px-6 rounded-lg transition-all text-sm flex items-center gap-2 border border-blue-500/30">"""

c = c.replace(old_btn, new_btn)

# Immutable Ledger styling
old_ledger = """      {/* LEDGER */}
      <div className="col-span-12 lg:col-span-9">
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-lg shadow-sm flex flex-col h-[calc(100vh-140px)]">
          <div className="px-5 py-4 border-b border-zinc-800/80">
            <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Immutable Ledger</h2>
          </div>
          <div className="overflow-auto flex-1">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="text-zinc-500 font-medium sticky top-0 bg-zinc-900/95 backdrop-blur-sm border-b border-zinc-800/80 z-10">"""

new_ledger = """      {/* LEDGER */}
      <div className="col-span-12 lg:col-span-9">
        <div className="glass-panel rounded-xl shadow-xl flex flex-col h-[calc(100vh-140px)] relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-zinc-800 via-blue-500/50 to-zinc-800 opacity-30"></div>
          <div className="px-6 py-5 border-b border-zinc-800/60 bg-zinc-900/40">
            <h2 className="text-xs font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              Immutable Operations Ledger
            </h2>
          </div>
          <div className="overflow-auto flex-1 custom-scrollbar">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="text-zinc-400 font-semibold sticky top-0 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/80 z-10 shadow-sm">"""

c = c.replace(old_ledger, new_ledger)

# Also fix the hover row
c = c.replace('className="hover:bg-zinc-800/20 transition-colors group"', 'className="hover:bg-zinc-800/40 transition-colors duration-200 group border-l-[3px] border-transparent hover:border-blue-500/50"')

with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as f:
    f.write(c)

