import { useEffect, useState } from "react"

export default function Splash({ onDone }) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => {
      setVisible(false)
      onDone()
    }, 2200)
    return () => clearTimeout(t)
  }, [])

  if (!visible) return null

  return (
    <div className="fixed inset-0 bg-dark-950 flex items-center justify-center z-50 flex-col gap-3">
      <div className="flex gap-1 items-end h-10">
        {[2, 3, 4, 5].map((h, i) => (
          <div key={i} className="w-2.5 rounded-sm animate-pulse"
            style={{
              height: `${h * 8}px`,
              backgroundColor: "#1D9E75",
              opacity: 0.4 + i * 0.15,
              animationDelay: `${i * 0.15}s`
            }} />
        ))}
      </div>
      <h1 className="text-white text-5xl font-medium tracking-tight">BLARE</h1>
      <p className="text-teal-700 text-xs tracking-widest">
        BOT-POWERED LIQUIDITY ANALYSIS & RISK EXECUTION
      </p>
    </div>
  )
}
