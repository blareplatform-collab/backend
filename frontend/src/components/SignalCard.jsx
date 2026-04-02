import { useTranslation } from "react-i18next"
import { useSignalStore } from "../store/signalStore"
import { useAppStore } from "../store/appStore"

const confidenceColor = (score) => {
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
    <div className="bg-dark-800 border border-dark-700 rounded-xl p-4 hover:border-teal-800 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-white font-medium text-lg">{signal.symbol}</span>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${isLong ? "bg-teal-900 text-teal-200" : "bg-red-900 text-red-200"}`}>
            {isLong ? t("signal.long") : t("signal.short")}
          </span>
          <span className="text-gray-500 text-xs">{signal.timeframe}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${confidenceColor(signal.confidence)}`}>
            {signal.confidence}/100
          </span>
          <span className="text-gray-600 text-xs">{signal.pattern}</span>
        </div>
      </div>

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

      {signal.ai_note && (
        <div className="bg-dark-900 border border-teal-900 rounded-lg p-3 mb-3">
          <div className="text-teal-600 text-xs mb-1">{t("signal.ai_note")}</div>
          <p className="text-gray-300 text-sm leading-relaxed">{signal.ai_note}</p>
        </div>
      )}

      {tradeMode === "semi" && isPending && (
        <div className="flex gap-2 mt-2">
          <button onClick={() => approveSignal(signal.id)}
            className="flex-1 bg-teal-600 hover:bg-teal-500 text-white rounded-lg py-2 text-sm font-medium transition-colors">
            {t("signal.approve")}
          </button>
          <button onClick={() => rejectSignal(signal.id)}
            className="flex-1 bg-dark-700 hover:bg-dark-600 text-gray-300 rounded-lg py-2 text-sm font-medium transition-colors">
            {t("signal.reject")}
          </button>
        </div>
      )}

      {!isPending && (
        <div className={`text-center text-xs py-1 rounded-lg mt-2 ${
          signal.status === "executed" ? "bg-teal-900 text-teal-300" :
          signal.status === "rejected" ? "bg-dark-700 text-gray-500" :
          "bg-dark-700 text-gray-400"}`}>
          {signal.status.toUpperCase()}
        </div>
      )}
    </div>
  )
}
