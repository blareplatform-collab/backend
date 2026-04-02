import { create } from "zustand"
import { subscribeToSignals } from "../utils/firestore"
import api from "../utils/api"

export const useSignalStore = create((set, get) => ({
  signals: [],
  loading: true,
  unsubscribe: null,

  startListening: () => {
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
