import { useEffect, useState } from "react"
import { useSignalStore } from "../store/signalStore"
import SignalCard from "../components/SignalCard"

const MARKETS = ["All", "Crypto", "Forex", "Indices", "Commodities"]

export default function Home() {
  const { signals, loading } = useSignalStore()
  const [market, setMarket] = useState("All")

  const filtered = market === "All"
    ? signals
    : signals.filter(s => s.market?.toLowerCase() === market.toLowerCase())

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-white text-xl font-medium">Live signals</h1>
        <div className="flex gap-1">
          {MARKETS.map(m => (
            <button key={m} onClick={() => setMarket(m)}
              className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                market === m
                  ? "bg-teal-900 text-teal-300"
                  : "text-gray-400 hover:text-white hover:bg-dark-700"}`}>
              {m}
            </button>
          ))}
        </div>
      </div>

      {loading && !signals.length && (
        <div className="text-center text-gray-600 py-20">Scanning markets...</div>
      )}

      <div className="flex flex-col gap-3">
        {filtered.map(signal => (
          <SignalCard key={signal.id} signal={signal} />
        ))}
      </div>

      {!loading && !filtered.length && (
        <div className="text-center text-gray-600 py-20">
          No signals yet — BLARE is scanning...
        </div>
      )}
    </div>
  )
}
