# BLARE — Session 08: Dashboard UI

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 07 complete

---

## Context

This session builds the full desktop + web dashboard.
Hybrid design — clean by default, deep on demand.
Teal accent, dark/light toggle, EN/ES/RO language support.
Every signal displays as a full breakdown card.

---

## Goals

- [ ] BLARE splash screen on startup
- [ ] Home page — live signals feed with full signal cards
- [ ] Chart view — TradingView Lightweight Charts
- [ ] Positions page — open trades + P&L
- [ ] Analytics page — win rate, R:R, drawdown, AI accuracy
- [ ] Settings page — profiles, API keys, strategies, theme, language
- [ ] Dark + Light theme toggle
- [ ] EN / ES / RO i18n
- [ ] Auto/Semi-auto mode toggle in navbar
- [ ] Real-time signal updates (polling every 30s)

---

## Step 1 — Tailwind + theme config

### frontend/tailwind.config.js
```js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        teal: {
          50:  "#E1F5EE",
          100: "#9FE1CB",
          200: "#5DCAA5",
          400: "#1D9E75",
          600: "#0F6E56",
          800: "#085041",
          900: "#04342C",
        },
        dark: {
          950: "#030a09",
          900: "#071210",
          800: "#0d1f1b",
          700: "#142b26",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      }
    }
  }
}
```

---

## Step 2 — i18n setup

### frontend/src/i18n/en.json
```json
{
  "nav": {
    "signals": "Signals",
    "chart": "Chart",
    "positions": "Positions",
    "analytics": "Analytics",
    "settings": "Settings"
  },
  "signal": {
    "long": "LONG",
    "short": "SHORT",
    "confidence": "Confidence",
    "entry": "Entry",
    "stop": "Stop",
    "target": "Target",
    "rr": "R:R",
    "approve": "Approve",
    "reject": "Reject",
    "pattern": "Pattern",
    "ai_note": "AI Analysis"
  },
  "mode": {
    "auto": "Full Auto",
    "semi": "Semi-Auto"
  },
  "settings": {
    "profile": "Profile",
    "api_keys": "API Keys",
    "strategies": "Strategies",
    "risk": "Risk Settings",
    "alerts": "Alerts",
    "language": "Language",
    "theme": "Theme"
  }
}
```

Copy structure to `es.json` (Spanish) and `ro.json` (Romanian) with translated values.

### frontend/src/i18n/index.js
```js
import i18n from "i18next"
import { initReactI18next } from "react-i18next"
import en from "./en.json"
import es from "./es.json"
import ro from "./ro.json"

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, es: { translation: es }, ro: { translation: ro } },
  lng: localStorage.getItem("blare_lang") || "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false }
})

export default i18n
```

---

## Step 3 — Zustand stores

### frontend/src/store/signalStore.js
```js
import { create } from "zustand"
import api from "../utils/api"

export const useSignalStore = create((set, get) => ({
  signals: [],
  loading: false,
  lastFetch: null,

  fetchSignals: async () => {
    set({ loading: true })
    try {
      const data = await api.get("/signals?limit=50")
      set({ signals: data.signals, loading: false, lastFetch: Date.now() })
    } catch (e) {
      set({ loading: false })
    }
  },

  approveSignal: async (id) => {
    await api.post(`/signals/${id}/approve`)
    get().fetchSignals()
  },

  rejectSignal: async (id) => {
    await api.post(`/signals/${id}/reject`)
    get().fetchSignals()
  },
}))
```

### frontend/src/store/appStore.js
```js
import { create } from "zustand"
import { persist } from "zustand/middleware"

export const useAppStore = create(persist(
  (set) => ({
    theme: "dark",
    language: "en",
    tradeMode: "semi",  // "auto" | "semi"
    activeProfile: "default",

    setTheme: (theme) => {
      set({ theme })
      document.documentElement.classList.toggle("dark", theme === "dark")
    },
    setLanguage: (language) => {
      set({ language })
      localStorage.setItem("blare_lang", language)
    },
    setTradeMode: (tradeMode) => set({ tradeMode }),
  }),
  { name: "blare-app-store" }
))
```

---

## Step 4 — Signal Card component

### frontend/src/components/SignalCard.jsx
```jsx
import { useTranslation } from "react-i18next"
import { useSignalStore } from "../store/signalStore"
import { useAppStore } from "../store/appStore"

const CONFIDENCE_COLOR = (score) => {
  if (score >= 86) return "text-teal-400"
  if (score >= 71) return "text-teal-200"
  if (score >= 51) return "text-yellow-400"
  return "text-gray-500"
}

export default function SignalCard({ signal }) {
  const { t } = useTranslation()
  const { approveSignal, rejectSignal } = useSignalStore()
  const { tradeMode } = useAppStore()

  const isLong = signal.direction === "long"
  const isPending = signal.status === "pending"

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-xl p-4 
                    hover:border-teal-800 transition-colors">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-white font-medium text-lg">{signal.symbol}</span>
          <span className={`px-2 py-0.5 rounded text-xs font-medium
            ${isLong 
              ? "bg-teal-900 text-teal-200" 
              : "bg-red-900 text-red-200"}`}>
            {isLong ? t("signal.long") : t("signal.short")}
          </span>
          <span className="text-gray-500 text-xs">{signal.timeframe}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${CONFIDENCE_COLOR(signal.confidence)}`}>
            {signal.confidence}/100
          </span>
          <span className="text-gray-600 text-xs">{signal.pattern}</span>
        </div>
      </div>

      {/* Trade levels */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        {[
          { label: t("signal.entry"), value: signal.entry, color: "text-white" },
          { label: t("signal.stop"), value: signal.stop, color: "text-red-400" },
          { label: t("signal.target"), value: signal.target, color: "text-teal-400" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-dark-900 rounded-lg p-2 text-center">
            <div className="text-gray-500 text-xs mb-1">{label}</div>
            <div className={`font-mono text-sm font-medium ${color}`}>
              {Number(value).toFixed(5)}
            </div>
          </div>
        ))}
      </div>

      {/* R:R + Position size */}
      <div className="flex gap-3 mb-3">
        <div className="bg-dark-900 rounded-lg px-3 py-1.5 text-center flex-1">
          <span className="text-gray-500 text-xs">{t("signal.rr")} </span>
          <span className="text-teal-400 text-sm font-medium">{signal.rr}:1</span>
        </div>
        <div className="bg-dark-900 rounded-lg px-3 py-1.5 text-center flex-1">
          <span className="text-gray-500 text-xs">Size </span>
          <span className="text-white text-sm font-medium">{signal.position_size_pct}%</span>
        </div>
        <div className="bg-dark-900 rounded-lg px-3 py-1.5 text-center flex-1">
          <span className="text-gray-500 text-xs">Market </span>
          <span className="text-gray-300 text-sm">{signal.market}</span>
        </div>
      </div>

      {/* AI Note */}
      {signal.ai_note && (
        <div className="bg-dark-900 border border-teal-900 rounded-lg p-3 mb-3">
          <div className="text-teal-600 text-xs mb-1">{t("signal.ai_note")}</div>
          <p className="text-gray-300 text-sm leading-relaxed">{signal.ai_note}</p>
        </div>
      )}

      {/* Approve/Reject (semi-auto + pending only) */}
      {tradeMode === "semi" && isPending && (
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => approveSignal(signal.id)}
            className="flex-1 bg-teal-600 hover:bg-teal-500 text-white 
                       rounded-lg py-2 text-sm font-medium transition-colors">
            {t("signal.approve")}
          </button>
          <button
            onClick={() => rejectSignal(signal.id)}
            className="flex-1 bg-dark-700 hover:bg-dark-600 text-gray-300 
                       rounded-lg py-2 text-sm font-medium transition-colors">
            {t("signal.reject")}
          </button>
        </div>
      )}

      {/* Status badge for non-pending */}
      {!isPending && (
        <div className={`text-center text-xs py-1 rounded-lg mt-2
          ${signal.status === "executed" ? "bg-teal-900 text-teal-300" :
            signal.status === "rejected" ? "bg-dark-700 text-gray-500" :
            "bg-dark-700 text-gray-400"}`}>
          {signal.status.toUpperCase()}
        </div>
      )}
    </div>
  )
}
```

---

## Step 5 — Navbar

### frontend/src/components/Navbar.jsx
```jsx
import { Link, useLocation } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useAppStore } from "../store/appStore"

export default function Navbar() {
  const { t } = useTranslation()
  const location = useLocation()
  const { theme, setTheme, tradeMode, setTradeMode } = useAppStore()

  const links = [
    { path: "/", label: t("nav.signals") },
    { path: "/chart", label: t("nav.chart") },
    { path: "/positions", label: t("nav.positions") },
    { path: "/analytics", label: t("nav.analytics") },
    { path: "/settings", label: t("nav.settings") },
  ]

  return (
    <nav className="bg-dark-900 border-b border-dark-700 px-6 py-3 
                    flex items-center justify-between">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="flex gap-0.5 items-end h-5">
          {[2, 3, 4, 5].map((h, i) => (
            <div key={i} className="w-1.5 bg-teal-400 rounded-sm"
                 style={{ height: `${h * 4}px`, opacity: 0.6 + i * 0.1 }} />
          ))}
        </div>
        <span className="text-white font-medium tracking-tight text-lg ml-1">
          BLARE
        </span>
      </div>

      {/* Nav links */}
      <div className="flex items-center gap-1">
        {links.map(({ path, label }) => (
          <Link key={path} to={path}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors
              ${location.pathname === path
                ? "bg-teal-900 text-teal-300"
                : "text-gray-400 hover:text-white hover:bg-dark-700"}`}>
            {label}
          </Link>
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        {/* Mode toggle */}
        <button
          onClick={() => setTradeMode(tradeMode === "auto" ? "semi" : "auto")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
            ${tradeMode === "auto"
              ? "bg-teal-600 text-white"
              : "bg-dark-700 text-gray-400"}`}>
          {tradeMode === "auto" ? t("mode.auto") : t("mode.semi")}
        </button>

        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="text-gray-400 hover:text-white transition-colors text-lg">
          {theme === "dark" ? "☀" : "◑"}
        </button>
      </div>
    </nav>
  )
}
```

---

## Step 6 — Home page (signals feed)

### frontend/src/pages/Home.jsx
```jsx
import { useEffect } from "react"
import { useSignalStore } from "../store/signalStore"
import SignalCard from "../components/SignalCard"

const MARKETS = ["All", "Crypto", "Forex", "Indices", "Commodities"]

export default function Home() {
  const { signals, loading, fetchSignals } = useSignalStore()

  useEffect(() => {
    fetchSignals()
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-white text-xl font-medium">Live signals</h1>
        <div className="flex gap-1">
          {MARKETS.map(m => (
            <button key={m}
              className="px-3 py-1 rounded-lg text-xs text-gray-400 
                         hover:text-white hover:bg-dark-700 transition-colors">
              {m}
            </button>
          ))}
        </div>
      </div>

      {loading && !signals.length && (
        <div className="text-center text-gray-600 py-20">Scanning markets...</div>
      )}

      <div className="flex flex-col gap-3">
        {signals.map(signal => (
          <SignalCard key={signal.id} signal={signal} />
        ))}
      </div>

      {!loading && !signals.length && (
        <div className="text-center text-gray-600 py-20">
          No signals yet — BLARE is scanning...
        </div>
      )}
    </div>
  )
}
```

---

## Step 7 — Splash screen

### frontend/src/components/Splash.jsx
```jsx
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
    <div className="fixed inset-0 bg-dark-950 flex items-center 
                    justify-center z-50 flex-col gap-3">
      <div className="flex gap-1 items-end h-10">
        {[2, 3, 4, 5].map((h, i) => (
          <div key={i}
            className="w-2.5 rounded-sm animate-pulse"
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
```

---

## Step 8 — App router

### frontend/src/App.jsx
```jsx
import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { useAppStore } from "./store/appStore"
import Navbar from "./components/Navbar"
import Splash from "./components/Splash"
import Home from "./pages/Home"
import Chart from "./pages/Chart"
import Positions from "./pages/Positions"
import Analytics from "./pages/Analytics"
import Settings from "./pages/Settings"
import "./i18n"

export default function App() {
  const [splashDone, setSplashDone] = useState(false)
  const { theme } = useAppStore()

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  return (
    <div className="min-h-screen bg-dark-950 dark:bg-dark-950">
      {!splashDone && <Splash onDone={() => setSplashDone(true)} />}
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chart" element={<Chart />} />
          <Route path="/positions" element={<Positions />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}
```

---

## Step 9 — Remaining pages (stubs — flesh out per page)

Create minimal stubs for `Chart.jsx`, `Positions.jsx`,
`Analytics.jsx`, `Settings.jsx` — each returns a page
container with the page title and "Coming in this session"
placeholder. Build each one out fully during this session.

Settings page must include:
- Profile name field
- Binance API key + secret fields (masked)
- OANDA API key field (masked)
- Risk % slider
- Auto/Semi toggle
- Strategy toggles (fetch from GET /strategies)
- Language selector (EN/ES/RO)
- Theme toggle

---

## Step 10 — Verify

```bash
cd frontend && npm run dev
# Check: splash screen shows on load
# Check: signals feed loads and auto-refreshes
# Check: signal cards show full breakdown
# Check: approve/reject works in semi-auto mode
# Check: dark/light toggle works
# Check: language switching works
```

Checklist:
- [ ] Splash screen shows on startup
- [ ] Signals feed loads with full signal cards
- [ ] Approve/reject fires correctly
- [ ] Dark + Light themes working
- [ ] EN/ES/RO language switching
- [ ] Mode toggle (auto/semi) visible in navbar
- [ ] Settings page saves profile + API keys

---

## Session 08 Complete

Commit message: `feat: session 08 — dashboard UI complete`

Next: **Session 09 — Mobile App**
