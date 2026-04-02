import { create } from "zustand"
import api from "../utils/api"

export const useSignalStore = create((set, get) => ({
  signals: [],
  loading: false,

  fetchSignals: async () => {
    set({ loading: true })
    try {
      const data = await api.get("/signals?limit=30")
      set({ signals: data.signals || [], loading: false })
    } catch {
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
