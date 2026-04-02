import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { useAppStore } from "./store/appStore"
import { useAuth } from "./hooks/useAuth"
import { useSignalStore } from "./store/signalStore"
import { requestNotificationPermission, setupForegroundNotifications } from "./utils/fcm"
import Navbar from "./components/Navbar"
import Splash from "./components/Splash"
import Login from "./pages/Login"
import Home from "./pages/Home"
import Chart from "./pages/Chart"
import Positions from "./pages/Positions"
import Analytics from "./pages/Analytics"
import Settings from "./pages/Settings"
import Backtest from "./pages/Backtest"
import "./i18n"

export default function App() {
  const [splashDone, setSplashDone] = useState(false)
  const { theme } = useAppStore()
  const { user, loading } = useAuth()
  const { startListening, stopListening } = useSignalStore()

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  useEffect(() => {
    if (user) {
      startListening()
      requestNotificationPermission()
      setupForegroundNotifications(() => {
        // Real-time listener handles updates automatically
      })
    }
    return () => stopListening()
  }, [user])

  if (loading) return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center">
      <div className="text-teal-400 text-sm">Loading...</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-dark-950">
      <BrowserRouter>
        {!user ? <Login /> : (
          <>
            {!splashDone && <Splash onDone={() => setSplashDone(true)} />}
            <Navbar />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/chart" element={<Chart />} />
              <Route path="/positions" element={<Positions />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/backtest" element={<Backtest />} />
            </Routes>
          </>
        )}
      </BrowserRouter>
    </div>
  )
}
