import { messaging as getMessaging } from "../config/firebase"
import { getToken, onMessage } from "firebase/messaging"
import { saveUserProfile } from "./firestore"

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY

export async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission()
    if (permission !== "granted") return null

    const m = await getMessaging()
    if (!m) return null

    const token = await getToken(m, { vapidKey: VAPID_KEY })
    if (token) {
      await saveUserProfile({ fcmToken: token })
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
    if (onSignal) onSignal(payload.data)
  })
}
