import { useState, useEffect, useRef } from "react"
import { createChart } from "lightweight-charts"
import api from "../utils/api"

const STRATEGIES = [
  "smc_fvg_entry", "smc_liquidity_sweep", "smc_order_block",
  "smc_choch_entry", "wyckoff_spring", "wyckoff_utad", "classic_double_bottom"
]
const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "EUR/USD", "GBP/USD", "SPX"]
const TIMEFRAMES = ["15m", "1h", "4h", "1d"]

export default function Backtest() {
  const [form, setForm] = useState({ strategy_id: STRATEGIES[0], symbol: SYMBOLS[0], timeframe: "4h" })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  const runBacktest = async () => {
    setLoading(true)
    try {
      const data = await api.post("/backtest/", form)
      setResult(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    if (!result?.metrics?.equity_curve || !chartRef.current) return
    if (chartInstance.current) { chartInstance.current.remove(); chartInstance.current = null }

    const chart = createChart(chartRef.current, {
      layout: { background: { color: "#0d1f1b" }, textColor: "#6b7280" },
      grid: { vertLines: { color: "#142b26" }, horzLines: { color: "#142b26" } },
      height: 220,
    })
    chartInstance.current = chart
    const series = chart.addLineSeries({ color: "#1D9E75", lineWidth: 2 })
    series.setData(result.metrics.equity_curve.map((v, i) => ({ time: i + 1, value: v })))
    chart.timeScale().fitContent()
  }, [result])

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-white text-xl font-medium mb-6">Backtest</h1>

      <div className="bg-dark-800 border border-dark-700 rounded-xl p-5 mb-6 grid grid-cols-2 gap-4">
        {[
          { label: "Strategy", key: "strategy_id", options: STRATEGIES },
          { label: "Symbol", key: "symbol", options: SYMBOLS },
          { label: "Timeframe", key: "timeframe", options: TIMEFRAMES },
        ].map(({ label, key, options }) => (
          <div key={key}>
            <label className="text-gray-500 text-xs mb-1 block">{label}</label>
            <select value={form[key]}
              onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              className="w-full bg-dark-900 text-white text-sm rounded-lg border border-dark-700 px-3 py-2 outline-none focus:border-teal-600">
              {options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        ))}
        <div className="col-span-2">
          <button onClick={runBacktest} disabled={loading}
            className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-medium transition-colors">
            {loading ? "Running backtest..." : "Run backtest"}
          </button>
        </div>
      </div>

      {result?.error && (
        <div className="bg-red-900 text-red-300 rounded-xl p-4 mb-4 text-sm">{result.error}</div>
      )}

      {result?.metrics && (
        <>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: "Total trades", value: result.metrics.total_trades },
              { label: "Win rate", value: `${result.metrics.win_rate}%` },
              { label: "Avg R:R", value: `${result.metrics.avg_rr}:1` },
              { label: "Max drawdown", value: `${result.metrics.max_drawdown_pct}%` },
              { label: "Profit factor", value: result.metrics.profit_factor },
              { label: "Total return", value: `${result.metrics.total_return_pct}%` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-dark-800 border border-dark-700 rounded-xl p-4 text-center">
                <div className="text-gray-500 text-xs mb-1">{label}</div>
                <div className="text-white font-medium text-lg">{value}</div>
              </div>
            ))}
          </div>

          <div className="bg-dark-800 border border-dark-700 rounded-xl p-4 mb-4">
            <div className="text-gray-500 text-xs mb-3">Equity curve</div>
            <div ref={chartRef} />
          </div>

          <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
            <div className="text-gray-500 text-xs mb-3">Trade log ({result.trades?.length} trades)</div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {result.trades?.map((t, i) => (
                <div key={i} className="flex justify-between text-xs py-1.5 border-b border-dark-700">
                  <span className="text-gray-400">{t.direction?.toUpperCase()}</span>
                  <span className={t.outcome === "win" ? "text-teal-400" : t.outcome === "loss" ? "text-red-400" : "text-gray-500"}>
                    {t.outcome} {t.pnl_r !== 0 ? `${t.pnl_r > 0 ? "+" : ""}${t.pnl_r}R` : ""}
                  </span>
                  <span className="text-gray-600">{t.bars_held} bars</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
