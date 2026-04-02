# BLARE — Session 09: Mobile App

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 08 complete

---

## Context

This session builds the React Native + Expo companion app.
Mobile = command center. Signals, alerts, one-tap approve/reject,
portfolio overview. Push notifications via Firebase Cloud Messaging.

---

## Goals

- [ ] Expo Router navigation (signals, positions, analytics, settings)
- [ ] Live signals feed with full signal cards
- [ ] One-tap approve/reject for semi-auto mode
- [ ] FCM push notifications on new signals
- [ ] Open positions + P&L view
- [ ] Analytics summary (key stats)
- [ ] Settings (profile, API keys, language, theme)
- [ ] Dark + light theme
- [ ] EN / ES / RO language support

---

## Step 1 — Dependencies

```bash
cd mobile
npx expo install expo-router expo-notifications
npx expo install @react-native-firebase/app @react-native-firebase/messaging
npx expo install expo-secure-store
npm install zustand axios i18next react-i18next
npm install @react-navigation/native react-native-safe-area-context
```

---

## Step 2 — FCM push notifications

### mobile/utils/notifications.js
```js
import * as Notifications from "expo-notifications"
import messaging from "@react-native-firebase/messaging"
import { Platform } from "react-native"

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
})

export async function registerForPushNotifications() {
  try {
    // Request permission
    const { status } = await Notifications.requestPermissionsAsync()
    if (status !== "granted") {
      console.log("[FCM] Notification permission denied")
      return null
    }

    // Get FCM token
    const token = await messaging().getToken()
    console.log("[FCM] Token:", token)
    return token
  } catch (e) {
    console.error("[FCM] Registration error:", e)
    return null
  }
}

export function setupNotificationListeners(onSignal) {
  // Foreground messages
  const unsubFG = messaging().onMessage(async (remoteMessage) => {
    console.log("[FCM] Foreground message:", remoteMessage)
    if (onSignal) onSignal(remoteMessage.data)
  })

  // Background/quit tap
  messaging().onNotificationOpenedApp((remoteMessage) => {
    if (onSignal) onSignal(remoteMessage.data)
  })

  return unsubFG
}
```

---

## Step 3 — API client

### mobile/utils/api.js
```js
import axios from "axios"

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "https://your-railway-url.railway.app"

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

api.interceptors.response.use(
  res => res.data,
  err => {
    console.error("[API Error]", err.message)
    return Promise.reject(err)
  }
)

export default api
```

### mobile/.env
```
EXPO_PUBLIC_API_URL=https://your-railway-url.railway.app
```

---

## Step 4 — Zustand store (mobile)

### mobile/store/signalStore.js
```js
import { create } from "zustand"
import api from "../utils/api"

export const useSignalStore = create((set, get) => ({
  signals: [],
  loading: false,

  fetchSignals: async () => {
    set({ loading: true })
    try {
      const data = await api.get("/signals?limit=30")
      set({ signals: data.signals, loading: false })
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

---

## Step 5 — Theme + i18n

### mobile/utils/theme.js
```js
export const colors = {
  teal400: "#1D9E75",
  teal200: "#5DCAA5",
  teal800: "#085041",
  dark950: "#030a09",
  dark900: "#071210",
  dark800: "#0d1f1b",
  dark700: "#142b26",
  white: "#ffffff",
  gray300: "#d1d5db",
  gray500: "#6b7280",
  gray600: "#4b5563",
  red400: "#f87171",
  yellow400: "#facc15",
}

export const typography = {
  h1: { fontSize: 28, fontWeight: "500", color: colors.white },
  h2: { fontSize: 20, fontWeight: "500", color: colors.white },
  body: { fontSize: 14, color: colors.gray300 },
  caption: { fontSize: 12, color: colors.gray500 },
  mono: { fontSize: 13, fontFamily: "monospace" },
}
```

---

## Step 6 — Signal Card (mobile)

### mobile/components/SignalCard.jsx
```jsx
import { View, Text, TouchableOpacity, StyleSheet } from "react-native"
import { colors, typography } from "../utils/theme"
import { useSignalStore } from "../store/signalStore"

const confidenceColor = (score) => {
  if (score >= 86) return colors.teal400
  if (score >= 71) return colors.teal200
  if (score >= 51) return colors.yellow400
  return colors.gray500
}

export default function SignalCard({ signal, tradeMode }) {
  const { approveSignal, rejectSignal } = useSignalStore()
  const isLong = signal.direction === "long"
  const isPending = signal.status === "pending"

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.row}>
        <View style={styles.row}>
          <Text style={styles.symbol}>{signal.symbol}</Text>
          <View style={[styles.badge,
            { backgroundColor: isLong ? "#085041" : "#450a0a" }]}>
            <Text style={{ color: isLong ? colors.teal200 : "#fca5a5",
                           fontSize: 11, fontWeight: "600" }}>
              {isLong ? "LONG" : "SHORT"}
            </Text>
          </View>
          <Text style={styles.caption}>{signal.timeframe}</Text>
        </View>
        <Text style={{ color: confidenceColor(signal.confidence),
                       fontSize: 13, fontWeight: "500" }}>
          {signal.confidence}/100
        </Text>
      </View>

      {/* Levels */}
      <View style={[styles.row, { marginTop: 10 }]}>
        {[
          { label: "Entry", value: signal.entry, color: colors.white },
          { label: "Stop",  value: signal.stop,  color: colors.red400 },
          { label: "Target", value: signal.target, color: colors.teal400 },
        ].map(({ label, value, color }) => (
          <View key={label} style={styles.levelBox}>
            <Text style={styles.caption}>{label}</Text>
            <Text style={[styles.mono, { color }]}>
              {Number(value).toFixed(5)}
            </Text>
          </View>
        ))}
      </View>

      {/* R:R + size */}
      <View style={[styles.row, { marginTop: 8 }]}>
        <Text style={styles.caption}>R:R </Text>
        <Text style={{ color: colors.teal400, fontSize: 13 }}>
          {signal.rr}:1
        </Text>
        <Text style={[styles.caption, { marginLeft: 16 }]}>Size </Text>
        <Text style={{ color: colors.white, fontSize: 13 }}>
          {signal.position_size_pct}%
        </Text>
      </View>

      {/* AI note */}
      {signal.ai_note ? (
        <View style={styles.aiBox}>
          <Text style={{ color: colors.teal800, fontSize: 11, marginBottom: 4 }}>
            AI Analysis
          </Text>
          <Text style={{ color: colors.gray300, fontSize: 13, lineHeight: 18 }}>
            {signal.ai_note}
          </Text>
        </View>
      ) : null}

      {/* Approve/Reject */}
      {tradeMode === "semi" && isPending && (
        <View style={[styles.row, { marginTop: 12, gap: 8 }]}>
          <TouchableOpacity
            style={[styles.btn, { backgroundColor: colors.teal800 }]}
            onPress={() => approveSignal(signal.id)}>
            <Text style={{ color: colors.teal200, fontWeight: "500" }}>
              Approve
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, { backgroundColor: "#1a1a1a" }]}
            onPress={() => rejectSignal(signal.id)}>
            <Text style={{ color: colors.gray500, fontWeight: "500" }}>
              Reject
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.dark800,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.dark700,
    padding: 14,
    marginBottom: 10,
  },
  row: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 8 },
  symbol: { color: colors.white, fontSize: 16, fontWeight: "500" },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  caption: { color: colors.gray500, fontSize: 12 },
  mono: { fontFamily: "monospace", fontSize: 12 },
  levelBox: {
    flex: 1, backgroundColor: colors.dark900,
    borderRadius: 8, padding: 8, alignItems: "center"
  },
  aiBox: {
    marginTop: 10, backgroundColor: colors.dark900,
    borderRadius: 8, borderWidth: 1,
    borderColor: "#142b26", padding: 10
  },
  btn: {
    flex: 1, padding: 10, borderRadius: 8, alignItems: "center"
  },
})
```

---

## Step 7 — Screens

### mobile/app/index.jsx — Signals feed
```jsx
import { useEffect } from "react"
import { View, FlatList, Text, StyleSheet, RefreshControl } from "react-native"
import { useSignalStore } from "../store/signalStore"
import SignalCard from "../components/SignalCard"
import { colors } from "../utils/theme"

export default function Signals() {
  const { signals, loading, fetchSignals } = useSignalStore()

  useEffect(() => {
    fetchSignals()
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live signals</Text>
      <FlatList
        data={signals}
        keyExtractor={s => s.id}
        renderItem={({ item }) => <SignalCard signal={item} tradeMode="semi" />}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={fetchSignals}
                          tintColor={colors.teal400} />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>Scanning markets...</Text>
        }
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  empty: { color: colors.gray600, textAlign: "center", marginTop: 60 },
})
```

### mobile/app/positions.jsx — Open positions
```jsx
import { useEffect, useState } from "react"
import { View, Text, FlatList, StyleSheet } from "react-native"
import api from "../utils/api"
import { colors } from "../utils/theme"

export default function Positions() {
  const [positions, setPositions] = useState([])

  useEffect(() => {
    api.get("/trades/open")
      .then(data => setPositions(data.positions))
      .catch(console.error)
  }, [])

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Open positions</Text>
      <FlatList
        data={positions}
        keyExtractor={p => p.signal_id || Math.random().toString()}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.symbol}>{item.symbol}</Text>
              <Text style={{ color: item.direction === "long"
                ? colors.teal400 : colors.red400, fontSize: 12 }}>
                {item.direction?.toUpperCase()}
              </Text>
            </View>
            <Text style={styles.caption}>Entry: {item.entry}</Text>
            <Text style={styles.caption}>Stop: {item.stop}</Text>
            <Text style={styles.caption}>Target: {item.target}</Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No open positions</Text>
        }
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  card: { backgroundColor: colors.dark800, borderRadius: 12,
          padding: 14, marginBottom: 10 },
  row: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  symbol: { color: colors.white, fontSize: 15, fontWeight: "500" },
  caption: { color: colors.gray500, fontSize: 12, marginTop: 2 },
  empty: { color: colors.gray600, textAlign: "center", marginTop: 60 },
})
```

---

## Step 8 — App layout with tab navigation

### mobile/app/_layout.jsx
```jsx
import { Tabs } from "expo-router"
import { colors } from "../utils/theme"

export default function Layout() {
  return (
    <Tabs screenOptions={{
      tabBarStyle: {
        backgroundColor: colors.dark900,
        borderTopColor: colors.dark700,
      },
      tabBarActiveTintColor: colors.teal400,
      tabBarInactiveTintColor: colors.gray600,
      headerStyle: { backgroundColor: colors.dark900 },
      headerTintColor: colors.white,
    }}>
      <Tabs.Screen name="index"
        options={{ title: "Signals", tabBarLabel: "Signals" }} />
      <Tabs.Screen name="positions"
        options={{ title: "Positions", tabBarLabel: "Positions" }} />
      <Tabs.Screen name="analytics"
        options={{ title: "Analytics", tabBarLabel: "Analytics" }} />
      <Tabs.Screen name="settings"
        options={{ title: "Settings", tabBarLabel: "Settings" }} />
    </Tabs>
  )
}
```

---

## Step 9 — Register FCM in app entry

Add to `mobile/app/_layout.jsx` useEffect:
```jsx
import { useEffect } from "react"
import { registerForPushNotifications,
         setupNotificationListeners } from "../utils/notifications"

// Inside Layout component:
useEffect(() => {
  registerForPushNotifications()
  const unsub = setupNotificationListeners((data) => {
    console.log("[App] New signal notification:", data)
  })
  return unsub
}, [])
```

---

## Step 10 — Verify

```bash
cd mobile
npx expo start

# Test on device or emulator:
# - Signals feed loads
# - Pull to refresh works
# - Approve/reject updates signal status
# - Push notification received when backend fires signal
```

Checklist:
- [ ] App boots without errors
- [ ] Signals feed loads from backend
- [ ] Pull-to-refresh works
- [ ] Signal cards show full breakdown
- [ ] Approve/reject works
- [ ] FCM notifications received on device
- [ ] Tab navigation smooth
- [ ] Dark theme consistent

---

## Session 09 Complete

Commit message: `feat: session 09 — mobile app complete`

Next: **Session 10 — Backtest + Analytics**
