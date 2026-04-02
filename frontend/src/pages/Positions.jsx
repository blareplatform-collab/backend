import { useEffect, useState } from "react"
import api from "../utils/api"

export default function Positions() {
  const [positions, setPositions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get("/trades/open")
      .then(data => setPositions(data.positions || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-white text-xl font-medium mb-6">Open Positions</h1>
      {loading && <div className="text-gray-600 text-center py-20">Loading...</div>}
      {!loading && !positions.length && (
        <div className="text-gray-600 text-center py-20">No open positions</div>
      )}
      <div className="flex flex-col gap-3">
        {positions.map((pos, i) => (
          <div key={i} className="bg-dark-800 border border-dark-700 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-white font-medium">{pos.symbol}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  pos.direction === "long" ? "bg-teal-900 text-teal-200" : "bg-red-900 text-red-200"}`}>
                  {pos.direction?.toUpperCase()}
                </span>
              </div>
              <span className={`text-sm font-medium ${(pos.pnl || 0) >= 0 ? "text-teal-400" : "text-red-400"}`}>
                {pos.pnl != null ? `${pos.pnl > 0 ? "+" : ""}${pos.pnl.toFixed(2)}` : "—"}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-3 text-xs">
              <div className="text-gray-500">Entry: <span className="text-gray-300 font-mono">{pos.entry?.toFixed(5)}</span></div>
              <div className="text-gray-500">Stop: <span className="text-red-400 font-mono">{pos.stop?.toFixed(5)}</span></div>
              <div className="text-gray-500">Target: <span className="text-teal-400 font-mono">{pos.target?.toFixed(5)}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
