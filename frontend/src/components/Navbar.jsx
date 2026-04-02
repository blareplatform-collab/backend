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
    { path: "/backtest", label: "Backtest" },
    { path: "/settings", label: t("nav.settings") },
  ]

  return (
    <nav className="bg-dark-900 border-b border-dark-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="flex gap-0.5 items-end h-5">
          {[2, 3, 4, 5].map((h, i) => (
            <div key={i} className="w-1.5 bg-teal-400 rounded-sm"
              style={{ height: `${h * 4}px`, opacity: 0.6 + i * 0.1 }} />
          ))}
        </div>
        <span className="text-white font-medium tracking-tight text-lg ml-1">BLARE</span>
      </div>

      <div className="flex items-center gap-1">
        {links.map(({ path, label }) => (
          <Link key={path} to={path}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              location.pathname === path
                ? "bg-teal-900 text-teal-300"
                : "text-gray-400 hover:text-white hover:bg-dark-700"}`}>
            {label}
          </Link>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => setTradeMode(tradeMode === "auto" ? "semi" : "auto")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            tradeMode === "auto" ? "bg-teal-600 text-white" : "bg-dark-700 text-gray-400"}`}>
          {tradeMode === "auto" ? t("mode.auto") : t("mode.semi")}
        </button>
        <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="text-gray-400 hover:text-white transition-colors text-lg">
          {theme === "dark" ? "☀" : "◑"}
        </button>
      </div>
    </nav>
  )
}
