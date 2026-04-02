import { create } from "zustand"
import { persist } from "zustand/middleware"

export const useAppStore = create(persist(
  (set) => ({
    theme: "dark",
    language: "en",
    tradeMode: "semi",
    activeProfile: "default",

    setTheme: (theme) => {
      set({ theme })
      document.documentElement.classList.toggle("dark", theme === "dark")
    },
    setLanguage: (language) => {
      set({ language })
      localStorage.setItem("blare_lang", language)
    },
    setTradeMode: (tradeMode) => set({ tradeMode }),
  }),
  { name: "blare-app-store" }
))
