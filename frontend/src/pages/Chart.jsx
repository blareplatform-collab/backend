import { useEffect, useRef, useState } from "react"
import { createChart } from "lightweight-charts"
import api from "../utils/api"

const CRYPTO = [
  "BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT",
  "ADA-USDT", "DOGE-USDT", "AVAX-USDT", "DOT-USDT", "MATIC-USDT",
  "LINK-USDT", "UNI-USDT", "ATOM-USDT", "LTC-USDT", "ETC-USDT",
]
const FOREX = ["EUR-USD", "GBP-USD", "USD-JPY", "AUD-USD", "USD-CAD", "USD-CHF", "NZD-USD"]
const TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]

const ALL_SYMBOLS = [...CRYPTO, ...FOREX]

export default function Chart() {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)
  const [symbol, setSymbol] = useState("BTC-USDT")
  const [timeframe, setTimeframe] = useState("1h")
  const [search, setSearch] = useState("")
  const [showDropdown, setShowDropdown] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!containerRef.current) return

    chartRef.current = createChart(containerRef.current, {
      layout: { background: { color: "#0d1f1b" }, textColor: "#9ca3af" },
      grid: { vertLines: { color: "#142b26" }, horzLines: { color: "#142b26" } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#142b26" },
      timeScale: { borderColor: "#142b26", timeVisible: true },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    })

    seriesRef.current = chartRef.current.addCandlestickSeries({
      upColor: "#1D9E75",
      downColor: "#ef4444",
      borderUpColor: "#1D9E75",
      borderDownColor: "#ef4444",
      wickUpColor: "#1D9E75",
      wickDownColor: "#ef4444",
    })

    const ro = new ResizeObserver(() => {
      if (chartRef.current && containerRef.current) {
        chartRef.current.resize(
          containerRef.current.clientWidth,
          containerRef.current.clientHeight
        )
      }
    })
    ro.observe(containerRef.current)

    return () => { ro.disconnect(); chartRef.current?.remove() }
  }, [])

  useEffect(() => {
    if (!seriesRef.current) return
    setLoading(true)
    setError("")
    api.get(`/candles/${symbol}?timeframe=${timeframe}&limit=300`)
      .then(data => {
        if (!seriesRef.current) return
        if (!data.candles?.length) { setError("No data available"); setLoading(false); return }
        const formatted = data.candles
          .map(c => ({ time: c.timestamp, open: c.open, high: c.high, low: c.low, close: c.close }))
          .sort((a, b) => a.time - b.time)
        seriesRef.current.setData(formatted)
        chartRef.current?.timeScale().fitContent()
        setLoading(false)
      })
      .catch(() => { setError("Failed to load candles"); setLoading(false) })
  }, [symbol, timeframe])

  const filtered = ALL_SYMBOLS.filter(s => s.toLowerCase().includes(search.toLowerCase()))

  const selectSymbol = (s) => {
    setSymbol(s)
    setSearch("")
    setShowDropdown(false)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-56px)]">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-dark-900 border-b border-dark-700 flex-wrap">

        {/* Symbol search */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(d => !d)}
            className="px-3 py-1.5 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm font-medium min-w-[110px] text-left hover:border-teal-600 transition-colors">
            {symbol}
          </button>
          {showDropdown && (
            <div className="absolute top-full left-0 mt-1 w-56 bg-dark-800 border border-dark-700 rounded-xl shadow-xl z-50">
              <div className="p-2 border-b border-dark-700">
                <input
                  autoFocus
                  placeholder="Search..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full bg-dark-900 text-white text-xs rounded-lg px-3 py-2 outline-none border border-dark-700 focus:border-teal-600 placeholder-gray-600"
                />
              </div>
              <div className="max-h-64 overflow-y-auto">
                {filtered.length === 0 && (
                  <div className="text-gray-600 text-xs px-3 py-2">No results</div>
                )}
                {CRYPTO.filter(s => s.toLowerCase().includes(search.toLowerCase())).length > 0 && (
                  <div className="px-3 py-1 text-gray-600 text-xs">CRYPTO</div>
                )}
                {CRYPTO.filter(s => s.toLowerCase().includes(search.toLowerCase())).map(s => (
                  <button key={s} onClick={() => selectSymbol(s)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-dark-700 transition-colors
                      ${symbol === s ? "text-teal-400" : "text-white"}`}>
                    {s}
                  </button>
                ))}
                {FOREX.filter(s => s.toLowerCase().includes(search.toLowerCase())).length > 0 && (
                  <div className="px-3 py-1 text-gray-600 text-xs border-t border-dark-700 mt-1">FOREX</div>
                )}
                {FOREX.filter(s => s.toLowerCase().includes(search.toLowerCase())).map(s => (
                  <button key={s} onClick={() => selectSymbol(s)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-dark-700 transition-colors
                      ${symbol === s ? "text-teal-400" : "text-white"}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="w-px h-4 bg-dark-700" />

        {/* Timeframes */}
        <div className="flex gap-1">
          {TIMEFRAMES.map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                timeframe === tf ? "bg-teal-900 text-teal-300" : "text-gray-400 hover:text-white hover:bg-dark-700"}`}>
              {tf}
            </button>
          ))}
        </div>

        {loading && <span className="text-gray-500 text-xs ml-2">Loading...</span>}
        {error && <span className="text-red-400 text-xs ml-2">{error}</span>}
      </div>

      {/* Chart */}
      <div ref={containerRef} className="flex-1" onClick={() => setShowDropdown(false)} />
    </div>
  )
}
