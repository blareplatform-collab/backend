import { useEffect, useState } from "react"
import api from "../utils/api"

export default function Analytics() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.get("/analytics/summary").then(setStats).catch(console.error)
  }, [])

  if (!stats) return (
    <div className="p-6 text-gray-600 text-center py-20">Loading analytics...</div>
  )

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-white text-xl font-medium mb-6">Analytics</h1>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {[
          { label: "Total trades", value: stats.total_trades ?? 0 },
          { label: "Win rate", value: `${stats.win_rate ?? 0}%` },
          { label: "Total P&L", value: `$${stats.total_pnl ?? 0}` },
          { label: "High conf signals", value: stats.high_conf_signals ?? 0 },
        ].map(({ label, value }) => (
          <div key={label} className="bg-dark-800 border border-dark-700 rounded-xl p-5">
            <div className="text-gray-500 text-xs mb-1">{label}</div>
            <div className="text-white text-2xl font-medium">{value}</div>
          </div>
        ))}
      </div>

      {stats.strategy_stats && Object.keys(stats.strategy_stats).length > 0 && (
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
          <div className="text-gray-500 text-xs mb-3">Win rate per strategy</div>
          {Object.entries(stats.strategy_stats).map(([sid, s]) => {
            const total = s.wins + s.losses
            const wr = total > 0 ? Math.round(s.wins / total * 100) : 0
            return (
              <div key={sid} className="flex items-center gap-3 py-2 border-b border-dark-700">
                <span className="text-gray-400 text-sm flex-1">{sid}</span>
                <div className="flex-1 bg-dark-900 rounded-full h-1.5">
                  <div className="bg-teal-400 h-1.5 rounded-full" style={{ width: `${wr}%` }} />
                </div>
                <span className="text-teal-400 text-sm w-10 text-right">{wr}%</span>
              </div>
            )
          })}
        </div>
      )}

      {!stats.total_trades && (
        <div className="text-center text-gray-600 py-12">
          No trades yet — run some backtests or let BLARE trade live.
        </div>
      )}
    </div>
  )
}
