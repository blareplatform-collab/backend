import { useEffect } from "react"
import { Tabs } from "expo-router"
import { colors } from "../utils/theme"
import { registerForPushNotifications, setupNotificationListeners } from "../utils/notifications"

export default function Layout() {
  useEffect(() => {
    registerForPushNotifications()
    const unsub = setupNotificationListeners((data) => {
      console.log("[App] New signal notification:", data)
    })
    return unsub
  }, [])

  return (
    <Tabs screenOptions={{
      tabBarStyle: { backgroundColor: colors.dark900, borderTopColor: colors.dark700 },
      tabBarActiveTintColor: colors.teal400,
      tabBarInactiveTintColor: colors.gray600,
      headerStyle: { backgroundColor: colors.dark900 },
      headerTintColor: colors.white,
    }}>
      <Tabs.Screen name="index" options={{ title: "Signals", tabBarLabel: "Signals" }} />
      <Tabs.Screen name="positions" options={{ title: "Positions", tabBarLabel: "Positions" }} />
      <Tabs.Screen name="analytics" options={{ title: "Analytics", tabBarLabel: "Analytics" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings", tabBarLabel: "Settings" }} />
    </Tabs>
  )
}
