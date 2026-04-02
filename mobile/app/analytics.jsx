import { useEffect, useState } from "react"
import { View, Text, StyleSheet, ScrollView } from "react-native"
import api from "../utils/api"
import { colors } from "../utils/theme"

export default function Analytics() {
  const [trades, setTrades] = useState([])

  useEffect(() => {
    api.get("/trades?limit=100")
      .then(data => setTrades(data.trades || []))
      .catch(console.error)
  }, [])

  const closed = trades.filter(t => t.status !== "open")
  const wins = closed.filter(t => (t.pnl || 0) > 0)
  const winRate = closed.length ? Math.round((wins.length / closed.length) * 100) : 0
  const avgRR = closed.length
    ? (closed.reduce((s, t) => s + (t.rr || 0), 0) / closed.length).toFixed(2)
    : "—"

  const stats = [
    { label: "Win Rate", value: `${winRate}%`, color: colors.teal400 },
    { label: "Avg R:R", value: avgRR, color: colors.white },
    { label: "Total Trades", value: String(closed.length), color: colors.white },
    { label: "Open", value: String(trades.filter(t => t.status === "open").length), color: colors.yellow400 },
  ]

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Analytics</Text>
      <View style={styles.grid}>
        {stats.map(({ label, value, color }) => (
          <View key={label} style={styles.statCard}>
            <Text style={styles.caption}>{label}</Text>
            <Text style={[styles.stat, { color }]}>{value}</Text>
          </View>
        ))}
      </View>
      <Text style={styles.empty}>Full equity curve — Session 10</Text>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  statCard: {
    width: "47%", backgroundColor: colors.dark800,
    borderRadius: 12, padding: 16, alignItems: "center"
  },
  caption: { color: colors.gray500, fontSize: 12, marginBottom: 6 },
  stat: { fontSize: 24, fontWeight: "500" },
  empty: { color: colors.gray600, textAlign: "center", marginTop: 40, fontSize: 13 },
})
