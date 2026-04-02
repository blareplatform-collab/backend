import * as Notifications from "expo-notifications"

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
})

export async function registerForPushNotifications() {
  try {
    const { status } = await Notifications.requestPermissionsAsync()
    if (status !== "granted") {
      console.log("[FCM] Notification permission denied")
      return null
    }
    const token = await Notifications.getExpoPushTokenAsync()
    console.log("[FCM] Token:", token.data)
    return token.data
  } catch (e) {
    console.error("[FCM] Registration error:", e)
    return null
  }
}

export function setupNotificationListeners(onSignal) {
  const sub = Notifications.addNotificationReceivedListener(notification => {
    const data = notification.request.content.data
    console.log("[FCM] Notification received:", data)
    if (onSignal) onSignal(data)
  })
  return () => sub.remove()
}
