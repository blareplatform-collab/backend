import { useState, useEffect } from "react"
import { auth } from "../config/firebase"
import { signOut } from "firebase/auth"
import { saveUserProfile, getUserProfile } from "../utils/firestore"
import { useNavigate } from "react-router-dom"

export default function Settings() {
  const navigate = useNavigate()
  const user = auth.currentUser
  const [profile, setProfile] = useState({
    name: "",
    binanceApiKey: "",
    binanceApiSecret: "",
    brokerApiKey: "",
    riskPct: 1.0,
    maxDailyLossPct: 3.0,
    tradeMode: "semi",
    language: "en",
    theme: "dark",
    alertEmail: true,
    alertPush: true,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    getUserProfile().then(data => {
      if (data) setProfile(prev => ({ ...prev, ...data }))
    })
  }, [])

  const save = async () => {
    setSaving(true)
    await saveUserProfile({
      ...profile,
      email: user?.email,
      userId: user?.uid,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleSignOut = async () => {
    await signOut(auth)
    navigate("/")
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-white text-xl font-medium">Settings</h1>
        <button onClick={handleSignOut}
          className="text-gray-500 hover:text-red-400 text-sm transition-colors">
          Sign out
        </button>
      </div>

      <div className="bg-dark-800 rounded-xl p-4 mb-4 border border-dark-700">
        <div className="text-gray-500 text-xs mb-1">Signed in as</div>
        <div className="text-white text-sm">{user?.email}</div>
      </div>

      <div className="bg-dark-800 rounded-xl p-5 mb-4 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">PROFILE</h2>
        <input
          placeholder="Your name"
          value={profile.name}
          onChange={e => setProfile(p => ({ ...p, name: e.target.value }))}
          className="w-full bg-dark-900 text-white text-sm rounded-xl border border-dark-700 px-4 py-3 outline-none focus:border-teal-600 placeholder-gray-600 mb-3"/>
      </div>

      <div className="bg-dark-800 rounded-xl p-5 mb-4 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">API KEYS</h2>
        <div className="space-y-3">
          {[
            { label: "Binance API Key", key: "binanceApiKey" },
            { label: "Binance API Secret", key: "binanceApiSecret" },
            { label: "Broker API Key (optional)", key: "brokerApiKey" },
          ].map(({ label, key }) => (
            <div key={key}>
              <label className="text-gray-500 text-xs mb-1 block">{label}</label>
              <input
                type="password"
                placeholder={`Enter ${label.toLowerCase()}`}
                value={profile[key]}
                onChange={e => setProfile(p => ({ ...p, [key]: e.target.value }))}
                className="w-full bg-dark-900 text-white text-sm rounded-xl border border-dark-700 px-4 py-3 outline-none focus:border-teal-600 placeholder-gray-600"/>
            </div>
          ))}
        </div>
        <p className="text-gray-600 text-xs mt-3">Keys are stored encrypted. Never shared with third parties.</p>
      </div>

      <div className="bg-dark-800 rounded-xl p-5 mb-4 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">RISK</h2>
        <div className="space-y-4">
          {[
            { label: "Risk per trade (%)", key: "riskPct", min: 0.1, max: 5, step: 0.1 },
            { label: "Max daily loss (%)", key: "maxDailyLossPct", min: 1, max: 10, step: 0.5 },
          ].map(({ label, key, min, max, step }) => (
            <div key={key}>
              <div className="flex justify-between mb-1">
                <label className="text-gray-500 text-xs">{label}</label>
                <span className="text-teal-400 text-xs">{profile[key]}%</span>
              </div>
              <input type="range" min={min} max={max} step={step}
                value={profile[key]}
                onChange={e => setProfile(p => ({ ...p, [key]: parseFloat(e.target.value) }))}
                className="w-full accent-teal-400"/>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-dark-800 rounded-xl p-5 mb-4 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">TRADE MODE</h2>
        <div className="flex gap-3">
          {[
            { value: "semi", label: "Semi-auto", desc: "You approve each trade" },
            { value: "auto", label: "Full auto", desc: "Fires automatically" },
          ].map(({ value, label, desc }) => (
            <button key={value}
              onClick={() => setProfile(p => ({ ...p, tradeMode: value }))}
              className={`flex-1 p-3 rounded-xl border text-left transition-colors
                ${profile.tradeMode === value
                  ? "border-teal-600 bg-teal-900/30"
                  : "border-dark-700 bg-dark-900"}`}>
              <div className="text-white text-sm font-medium">{label}</div>
              <div className="text-gray-500 text-xs mt-0.5">{desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-dark-800 rounded-xl p-5 mb-6 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">PREFERENCES</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Language</span>
            <select value={profile.language}
              onChange={e => setProfile(p => ({ ...p, language: e.target.value }))}
              className="bg-dark-900 text-white text-sm rounded-lg border border-dark-700 px-3 py-1.5 outline-none">
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="ro">Română</option>
            </select>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Theme</span>
            <select value={profile.theme}
              onChange={e => setProfile(p => ({ ...p, theme: e.target.value }))}
              className="bg-dark-900 text-white text-sm rounded-lg border border-dark-700 px-3 py-1.5 outline-none">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>
          {[
            { label: "Email alerts", key: "alertEmail" },
            { label: "Push notifications", key: "alertPush" },
          ].map(({ label, key }) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">{label}</span>
              <button
                onClick={() => setProfile(p => ({ ...p, [key]: !p[key] }))}
                className={`w-10 h-6 rounded-full transition-colors relative ${profile[key] ? "bg-teal-600" : "bg-dark-700"}`}>
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${profile[key] ? "left-5" : "left-1"}`}/>
              </button>
            </div>
          ))}
        </div>
      </div>

      <button onClick={save} disabled={saving}
        className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white rounded-xl py-3 font-medium transition-colors">
        {saving ? "Saving..." : saved ? "Saved!" : "Save settings"}
      </button>
    </div>
  )
}
