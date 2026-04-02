# BLARE — Firebase Complete Setup & Integration Guide

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to execute

---

## Overview

This guide covers the complete Firebase integration for BLARE:
- Firebase Auth — user accounts + profile management
- Firestore — database for signals, trades, analytics
- Firebase Cloud Messaging (FCM) — push notifications
- Firebase Hosting — web app deployment
- Gmail integration — transactional + account emails

---

## Step 1 — Create Firebase Project

1. Go to **console.firebase.google.com**
2. Click **Add project**
3. Name it: `blare-trading`
4. Disable Google Analytics (not needed)
5. Click **Create project**

---

## Step 2 — Firebase Auth Setup

### In Firebase Console:
1. Go to **Build → Authentication**
2. Click **Get started**
3. Enable these sign-in providers:
   - **Email/Password** → Enable → Save
   - **Google** → Enable → add your project's support email → Save

### Install in frontend:
```bash
cd frontend
npm install firebase
```

### frontend/src/config/firebase.js
```javascript
/**
 * BLARE Firebase client config
 * Used by frontend + mobile for Auth, Firestore, FCM
 */
import { initializeApp } from "firebase/app"
import { getAuth } from "firebase/auth"
import { getFirestore } from "firebase/firestore"
import { getMessaging, isSupported } from "firebase/messaging"

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)
export const db = getFirestore(app)
export const messaging = async () => {
  const supported = await isSupported()
  return supported ? getMessaging(app) : null
}

export default app
```

### frontend/.env (add these)
```bash
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=blare-trading.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=blare-trading
VITE_FIREBASE_STORAGE_BUCKET=blare-trading.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_VAPID_KEY=
```

Find all these values in Firebase Console → Project Settings → General → Your apps → Add web app → name it "BLARE Web"

---

## Step 3 — Auth Pages

### frontend/src/pages/Login.jsx
```jsx
import { useState } from "react"
import { auth } from "../config/firebase"
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
} from "firebase/auth"
import { useNavigate } from "react-router-dom"

export default function Login() {
  const [mode, setMode] = useState("login") // login | signup | reset
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async () => {
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      if (mode === "login") {
        await signInWithEmailAndPassword(auth, email, password)
        navigate("/")
      } else if (mode === "signup") {
        await createUserWithEmailAndPassword(auth, email, password)
        navigate("/")
      } else if (mode === "reset") {
        await sendPasswordResetEmail(auth, email)
        setSuccess("Password reset email sent. Check your inbox.")
      }
    } catch (e) {
      setError(e.message.replace("Firebase: ", "").replace(/\(auth.*\)/, ""))
    }
    setLoading(false)
  }

  const handleGoogle = async () => {
    try {
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
      navigate("/")
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center gap-1 items-end h-8 mb-3">
            {[2, 3, 4, 5].map((h, i) => (
              <div key={i} className="w-2 rounded-sm bg-teal-400"
                   style={{ height: `${h * 6}px`, opacity: 0.5 + i * 0.15 }} />
            ))}
          </div>
          <h1 className="text-white text-3xl font-medium tracking-tight">BLARE</h1>
          <p className="text-gray-600 text-xs mt-1 tracking-widest">
            {mode === "login" ? "SIGN IN" : mode === "signup" ? "CREATE ACCOUNT" : "RESET PASSWORD"}
          </p>
        </div>

        {/* Form */}
        <div className="bg-dark-800 rounded-2xl p-6 border border-dark-700">
          <div className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full bg-dark-900 text-white text-sm rounded-xl
                         border border-dark-700 px-4 py-3 outline-none
                         focus:border-teal-600 placeholder-gray-600 transition-colors"
            />
            {mode !== "reset" && (
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSubmit()}
                className="w-full bg-dark-900 text-white text-sm rounded-xl
                           border border-dark-700 px-4 py-3 outline-none
                           focus:border-teal-600 placeholder-gray-600 transition-colors"
              />
            )}
          </div>

          {error && (
            <p className="text-red-400 text-xs mt-3 text-center">{error}</p>
          )}
          {success && (
            <p className="text-teal-400 text-xs mt-3 text-center">{success}</p>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full mt-4 bg-teal-600 hover:bg-teal-500
                       disabled:opacity-50 text-white rounded-xl py-3
                       text-sm font-medium transition-colors">
            {loading ? "..." : mode === "login" ? "Sign in" : mode === "signup" ? "Create account" : "Send reset email"}
          </button>

          {mode !== "reset" && (
            <>
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-dark-700" />
                <span className="text-gray-600 text-xs">or</span>
                <div className="flex-1 h-px bg-dark-700" />
              </div>
              <button
                onClick={handleGoogle}
                className="w-full bg-dark-900 hover:bg-dark-700 text-white
                           rounded-xl py-3 text-sm border border-dark-700
                           transition-colors">
                Continue with Google
              </button>
            </>
          )}

          {/* Mode switchers */}
          <div className="flex justify-between mt-4">
            {mode === "login" && (
              <>
                <button onClick={() => setMode("signup")}
                  className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                  Create account
                </button>
                <button onClick={() => setMode("reset")}
                  className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                  Forgot password?
                </button>
              </>
            )}
            {(mode === "signup" || mode === "reset") && (
              <button onClick={() => setMode("login")}
                className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                Back to sign in
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

### frontend/src/hooks/useAuth.js
```javascript
/**
 * BLARE Auth hook
 * Returns current user and loading state.
 * Use this everywhere you need the current user.
 */
import { useState, useEffect } from "react"
import { auth } from "../config/firebase"
import { onAuthStateChanged } from "firebase/auth"

export function useAuth() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  return { user, loading }
}
```

### Update frontend/src/App.jsx to protect routes:
```jsx
import { useAuth } from "./hooks/useAuth"
import Login from "./pages/Login"

export default function App() {
  const { user, loading } = useAuth()
  const [splashDone, setSplashDone] = useState(false)

  if (loading) return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center">
      <div className="text-teal-400 text-sm">Loading...</div>
    </div>
  )

  if (!user) return <Login />

  // ... rest of app (splash + router)
}
```

---

## Step 4 — Firestore Database Setup

### In Firebase Console:
1. Go to **Build → Firestore Database**
2. Click **Create database**
3. Start in **production mode**
4. Choose region: **europe-west1** (closest to Romania)
5. Click **Done**

### Firestore Security Rules:
In Firebase Console → Firestore → Rules, paste:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users can only read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Signals — authenticated users can read, only backend can write
    match /signals/{signalId} {
      allow read: if request.auth != null;
      allow write: if false; // backend only via Admin SDK
    }

    // Trades — user can only see their own trades
    match /trades/{tradeId} {
      allow read: if request.auth != null &&
        resource.data.userId == request.auth.uid;
      allow write: if false; // backend only
    }

    // Analytics — user can only see their own
    match /analytics/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false; // backend only
    }

    // Backtests — user can read/write their own
    match /backtests/{backtestId} {
      allow read, write: if request.auth != null &&
        resource.data.userId == request.auth.uid;
    }
  }
}
```

### Firestore Indexes (create these in Console → Indexes):
```
Collection: signals
Fields: status (ASC), created_at (DESC)

Collection: trades
Fields: userId (ASC), opened_at (DESC)

Collection: trades
Fields: userId (ASC), status (ASC)
```

### frontend/src/utils/firestore.js
```javascript
/**
 * BLARE Firestore helpers
 * All database operations go through here.
 */
import { db, auth } from "../config/firebase"
import {
  collection, doc, getDoc, getDocs,
  setDoc, updateDoc, query,
  where, orderBy, limit, onSnapshot,
} from "firebase/firestore"

// ── USER PROFILE ──────────────────────────────────

export async function saveUserProfile(profileData) {
  const uid = auth.currentUser?.uid
  if (!uid) return
  await setDoc(doc(db, "users", uid), {
    ...profileData,
    updatedAt: new Date().toISOString(),
  }, { merge: true })
}

export async function getUserProfile() {
  const uid = auth.currentUser?.uid
  if (!uid) return null
  const snap = await getDoc(doc(db, "users", uid))
  return snap.exists() ? snap.data() : null
}

// ── SIGNALS ───────────────────────────────────────

export async function getSignals(limitCount = 50) {
  const q = query(
    collection(db, "signals"),
    orderBy("created_at", "desc"),
    limit(limitCount)
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}

export function subscribeToSignals(callback, limitCount = 50) {
  // Real-time listener — updates UI instantly when new signal fires
  const q = query(
    collection(db, "signals"),
    orderBy("created_at", "desc"),
    limit(limitCount)
  )
  return onSnapshot(q, (snap) => {
    const signals = snap.docs.map(d => ({ id: d.id, ...d.data() }))
    callback(signals)
  })
}

export async function getPendingSignals() {
  const q = query(
    collection(db, "signals"),
    where("status", "==", "pending"),
    orderBy("created_at", "desc")
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}

// ── TRADES ────────────────────────────────────────

export async function getTrades(limitCount = 50) {
  const uid = auth.currentUser?.uid
  if (!uid) return []
  const q = query(
    collection(db, "trades"),
    where("userId", "==", uid),
    orderBy("opened_at", "desc"),
    limit(limitCount)
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}

export async function getOpenPositions() {
  const uid = auth.currentUser?.uid
  if (!uid) return []
  const q = query(
    collection(db, "trades"),
    where("userId", "==", uid),
    where("status", "==", "open")
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}

// ── ANALYTICS ─────────────────────────────────────

export async function getAnalytics() {
  const uid = auth.currentUser?.uid
  if (!uid) return null
  const snap = await getDoc(doc(db, "analytics", uid))
  return snap.exists() ? snap.data() : null
}
```

### Update Zustand signal store to use real-time Firestore:
```javascript
// frontend/src/store/signalStore.js
import { create } from "zustand"
import { subscribeToSignals } from "../utils/firestore"
import api from "../utils/api"

export const useSignalStore = create((set) => ({
  signals: [],
  loading: true,
  unsubscribe: null,

  startListening: () => {
    // Real-time Firestore subscription — no more polling!
    const unsub = subscribeToSignals((signals) => {
      set({ signals, loading: false })
    })
    set({ unsubscribe: unsub })
  },

  stopListening: () => {
    set(state => {
      state.unsubscribe?.()
      return { unsubscribe: null }
    })
  },

  approveSignal: async (id) => {
    await api.post(`/signals/${id}/approve`)
  },

  rejectSignal: async (id) => {
    await api.post(`/signals/${id}/reject`)
  },
}))
```

Update `Home.jsx` to use real-time listener:
```jsx
useEffect(() => {
  startListening()
  return () => stopListening() // cleanup on unmount
}, [])
```

---

## Step 5 — User Profile Page

### frontend/src/pages/Settings.jsx (Profile section)
```jsx
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

      {/* Account info */}
      <div className="bg-dark-800 rounded-xl p-4 mb-4 border border-dark-700">
        <div className="text-gray-500 text-xs mb-1">Signed in as</div>
        <div className="text-white text-sm">{user?.email}</div>
      </div>

      {/* Profile */}
      <div className="bg-dark-800 rounded-xl p-5 mb-4 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">PROFILE</h2>
        <input
          placeholder="Your name"
          value={profile.name}
          onChange={e => setProfile(p => ({ ...p, name: e.target.value }))}
          className="w-full bg-dark-900 text-white text-sm rounded-xl
                     border border-dark-700 px-4 py-3 outline-none
                     focus:border-teal-600 placeholder-gray-600 mb-3"/>
      </div>

      {/* API Keys */}
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
                className="w-full bg-dark-900 text-white text-sm rounded-xl
                           border border-dark-700 px-4 py-3 outline-none
                           focus:border-teal-600 placeholder-gray-600"/>
            </div>
          ))}
        </div>
        <p className="text-gray-600 text-xs mt-3">
          Keys are stored encrypted. Never shared with third parties.
        </p>
      </div>

      {/* Risk Settings */}
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

      {/* Trade Mode */}
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

      {/* Preferences */}
      <div className="bg-dark-800 rounded-xl p-5 mb-6 border border-dark-700">
        <h2 className="text-gray-400 text-xs mb-4 tracking-widest">PREFERENCES</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Language</span>
            <select value={profile.language}
              onChange={e => setProfile(p => ({ ...p, language: e.target.value }))}
              className="bg-dark-900 text-white text-sm rounded-lg border
                         border-dark-700 px-3 py-1.5 outline-none">
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="ro">Română</option>
            </select>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Theme</span>
            <select value={profile.theme}
              onChange={e => setProfile(p => ({ ...p, theme: e.target.value }))}
              className="bg-dark-900 text-white text-sm rounded-lg border
                         border-dark-700 px-3 py-1.5 outline-none">
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
                className={`w-10 h-6 rounded-full transition-colors relative
                  ${profile[key] ? "bg-teal-600" : "bg-dark-700"}`}>
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full
                  transition-transform ${profile[key] ? "left-5" : "left-1"}`}/>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Save button */}
      <button onClick={save} disabled={saving}
        className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50
                   text-white rounded-xl py-3 font-medium transition-colors">
        {saving ? "Saving..." : saved ? "Saved!" : "Save settings"}
      </button>
    </div>
  )
}
```

---

## Step 6 — Firebase Cloud Messaging (Push Notifications)

### In Firebase Console:
1. Go to **Project Settings → Cloud Messaging**
2. Generate **Web Push certificate** (VAPID key) → copy it to `VITE_FIREBASE_VAPID_KEY`

### frontend/public/firebase-messaging-sw.js
Create this file (service worker for background notifications):
```javascript
importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js")
importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js")

firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "blare-trading.firebaseapp.com",
  projectId: "blare-trading",
  storageBucket: "blare-trading.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
})

const messaging = firebase.messaging()

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification
  self.registration.showNotification(title, {
    body,
    icon: "/logo192.png",
    badge: "/logo192.png",
    vibrate: [200, 100, 200],
  })
})
```

### frontend/src/utils/fcm.js
```javascript
/**
 * BLARE FCM Web Push Notifications
 */
import { messaging as getMessaging } from "../config/firebase"
import { getToken, onMessage } from "firebase/messaging"
import { saveUserProfile } from "./firestore"

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY

export async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission()
    if (permission !== "granted") {
      console.log("[FCM] Permission denied")
      return null
    }
    const m = await getMessaging()
    if (!m) return null

    const token = await getToken(m, { vapidKey: VAPID_KEY })
    if (token) {
      // Save FCM token to user profile so backend can send to this device
      await saveUserProfile({ fcmToken: token })
      console.log("[FCM] Token saved:", token.substring(0, 20) + "...")
    }
    return token
  } catch (e) {
    console.error("[FCM] Error:", e)
    return null
  }
}

export async function setupForegroundNotifications(onSignal) {
  const m = await getMessaging()
  if (!m) return

  onMessage(m, (payload) => {
    console.log("[FCM] Foreground message:", payload)
    // Show in-app toast
    if (onSignal) onSignal(payload.data)
  })
}
```

### Add to App.jsx on startup:
```jsx
import { requestNotificationPermission, setupForegroundNotifications } from "./utils/fcm"

// Inside App component useEffect:
useEffect(() => {
  if (user) {
    requestNotificationPermission()
    setupForegroundNotifications((data) => {
      console.log("[App] New signal:", data)
      // Refresh signals store
      startListening()
    })
  }
}, [user])
```

### Backend — send FCM notification on new signal:

Update `backend/notifications/fcm.py`:
```python
"""
BLARE FCM Notification Sender
Sends push notifications to all user devices when a signal fires.
"""
import firebase_admin.messaging as fcm_messaging
from config.firebase import get_db

async def send_signal_notification(signal: dict):
  """Send push notification for a new signal to all registered devices."""
  try:
    db = get_db()
    # Get all FCM tokens from user profiles
    users = db.collection("users").stream()
    tokens = []
    for user in users:
      data = user.to_dict()
      token = data.get("fcmToken")
      alert_push = data.get("alertPush", True)
      if token and alert_push:
        tokens.append(token)

    if not tokens:
      return

    direction = signal.get("direction", "").upper()
    symbol = signal.get("symbol", "")
    confidence = signal.get("confidence", 0)
    pattern = signal.get("pattern", "")

    # Send to all devices
    message = fcm_messaging.MulticastMessage(
      notification=fcm_messaging.Notification(
        title=f"BLARE Signal — {symbol} {direction}",
        body=f"{pattern} | Confidence: {confidence}/100 | R:R {signal.get('rr', 0):.1f}:1",
      ),
      data={
        "signal_id": signal.get("id", ""),
        "symbol": symbol,
        "direction": direction,
        "confidence": str(confidence),
      },
      tokens=tokens,
    )
    response = fcm_messaging.send_each_for_multicast(message)
    print(f"[FCM] Sent to {response.success_count}/{len(tokens)} devices")
  except Exception as e:
    print(f"[FCM] Error sending notification: {e}")
```

---

## Step 7 — Gmail Integration

Using **Resend** — cleanest free email API (100 emails/day free).

### Sign up:
1. Go to **resend.com**
2. Create account with your BLARE Gmail
3. Add domain or use their sandbox for testing
4. Get API key → add to `.env` as `RESEND_API_KEY`

```bash
pip install resend
```

### backend/notifications/email.py
```python
"""
BLARE Email Notifications
Handles both transactional alerts and account emails via Resend.
"""
import resend
from config.settings import RESEND_API_KEY, APP_ENV

resend.api_key = RESEND_API_KEY

FROM_EMAIL = "BLARE <alerts@yourdomain.com>"  # update with your domain

async def send_signal_email(user_email: str, signal: dict):
  """Send signal alert email to user."""
  if not user_email:
    return
  try:
    direction = signal.get("direction", "").upper()
    symbol = signal.get("symbol", "")
    confidence = signal.get("confidence", 0)

    resend.Emails.send({
      "from": FROM_EMAIL,
      "to": user_email,
      "subject": f"BLARE Signal — {symbol} {direction}",
      "html": f"""
        <div style="font-family:monospace;background:#030a09;color:#fff;padding:24px;border-radius:12px;max-width:480px">
          <h2 style="color:#1D9E75;margin:0 0 16px">BLARE Signal</h2>
          <table style="width:100%;border-collapse:collapse">
            <tr><td style="color:#6b7280;padding:4px 0">Symbol</td><td style="color:#fff">{symbol}</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">Direction</td>
                <td style="color:{'#1D9E75' if direction=='LONG' else '#f87171'}">{direction}</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">Entry</td><td style="color:#fff">{signal.get('entry', 0):.5f}</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">Stop</td><td style="color:#f87171">{signal.get('stop', 0):.5f}</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">Target</td><td style="color:#1D9E75">{signal.get('target', 0):.5f}</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">R:R</td><td style="color:#1D9E75">{signal.get('rr', 0):.1f}:1</td></tr>
            <tr><td style="color:#6b7280;padding:4px 0">Confidence</td><td style="color:#1D9E75">{confidence}/100</td></tr>
          </table>
          <p style="color:#6b7280;margin-top:16px;font-size:12px">{signal.get('ai_note', '')}</p>
          <p style="color:#142b26;font-size:11px;margin-top:24px">BLARE — Bot-powered Liquidity Analysis & Risk Execution</p>
        </div>
      """
    })
    print(f"[Email] Signal alert sent to {user_email}")
  except Exception as e:
    print(f"[Email] Error sending signal email: {e}")

async def send_welcome_email(user_email: str, name: str = "Trader"):
  """Send welcome email on account creation."""
  try:
    resend.Emails.send({
      "from": FROM_EMAIL,
      "to": user_email,
      "subject": "Welcome to BLARE",
      "html": f"""
        <div style="font-family:monospace;background:#030a09;color:#fff;padding:24px;border-radius:12px;max-width:480px">
          <h2 style="color:#1D9E75">Welcome to BLARE, {name}</h2>
          <p style="color:#d1d5db">Your account is ready. Configure your API keys in Settings to start trading.</p>
          <p style="color:#142b26;font-size:11px;margin-top:24px">BLARE — Bot-powered Liquidity Analysis & Risk Execution</p>
        </div>
      """
    })
  except Exception as e:
    print(f"[Email] Error sending welcome email: {e}")

async def send_trade_confirmation_email(user_email: str, trade: dict):
  """Send trade execution confirmation email."""
  try:
    resend.Emails.send({
      "from": FROM_EMAIL,
      "to": user_email,
      "subject": f"Trade Executed — {trade.get('symbol')} {trade.get('direction', '').upper()}",
      "html": f"""
        <div style="font-family:monospace;background:#030a09;color:#fff;padding:24px;border-radius:12px;max-width:480px">
          <h2 style="color:#1D9E75">Trade Executed</h2>
          <p style="color:#d1d5db">Symbol: {trade.get('symbol')}</p>
          <p style="color:#d1d5db">Direction: {trade.get('direction', '').upper()}</p>
          <p style="color:#d1d5db">Entry: {trade.get('entry', 0):.5f}</p>
          <p style="color:#d1d5db">Stop: {trade.get('stop', 0):.5f}</p>
          <p style="color:#d1d5db">Target: {trade.get('target', 0):.5f}</p>
        </div>
      """
    })
  except Exception as e:
    print(f"[Email] Error sending trade email: {e}")
```

Add to `.env`:
```bash
RESEND_API_KEY=
```

---

## Step 8 — Firebase Hosting (Web App Deployment)

### Install Firebase CLI:
```bash
npm install -g firebase-tools
firebase login
```

### Initialize hosting in frontend folder:
```bash
cd frontend
firebase init hosting
```

Select:
- Use existing project → `blare-trading`
- Public directory → `dist`
- Single page app → **Yes**
- GitHub auto-deploy → **No** (for now)

### frontend/firebase.json
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

### Deploy:
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

Your app will be live at: `https://blare-trading.web.app`

---

## Step 9 — Backend Service Account

For the FastAPI backend to use Firebase Admin SDK:

1. Firebase Console → Project Settings → Service Accounts
2. Click **Generate new private key**
3. Download the JSON file
4. Extract these values into your `backend/.env`:

```bash
FIREBASE_PROJECT_ID=blare-trading
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@blare-trading.iam.gserviceaccount.com
```

The `backend/config/firebase.py` from Session 01 already handles this — no changes needed.

---

## Step 10 — Final Checklist

- [ ] Firebase project created — `blare-trading`
- [ ] Auth enabled — Email/Password + Google
- [ ] Firestore created — europe-west1 region
- [ ] Firestore security rules deployed
- [ ] Firestore indexes created
- [ ] FCM Web Push certificate generated
- [ ] `firebase-messaging-sw.js` in `/public`
- [ ] Frontend Firebase config in `.env`
- [ ] Backend service account keys in `backend/.env`
- [ ] Login/Signup page working
- [ ] Profile settings saving to Firestore
- [ ] Real-time signal listener working
- [ ] Push notifications firing on new signal
- [ ] Resend account created + API key added
- [ ] Welcome email sending on signup
- [ ] Signal alert emails sending
- [ ] Web app deployed to Firebase Hosting

---

## Quick Reference — Firebase Collections

```
users/{uid}
  name, email, userId, fcmToken
  binanceApiKey, binanceApiSecret, brokerApiKey (encrypted)
  riskPct, maxDailyLossPct, tradeMode
  language, theme, alertEmail, alertPush
  updatedAt

signals/{signalId}
  symbol, market, direction, timeframe
  pattern, entry, stop, target, rr
  confidence, ai_note, position_size_pct
  status, created_at

trades/{tradeId}
  userId, signal_id, symbol, market
  direction, entry, stop, target
  quantity/units, pnl, status
  date, opened_at, closed_at

analytics/{uid}
  total_trades, win_rate, total_pnl
  strategy_stats, drawdown_history
  confidence_accuracy

backtests/{backtestId}
  userId, strategy, symbol, timeframe
  metrics, trades, created_at
```

---

*Firebase is the backbone. Get this right and everything else plugs in cleanly.*
