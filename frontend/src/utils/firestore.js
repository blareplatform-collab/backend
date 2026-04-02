import { db, auth } from "../config/firebase"
import {
  collection, doc, getDoc, getDocs,
  setDoc, query, where, orderBy, limit, onSnapshot,
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
