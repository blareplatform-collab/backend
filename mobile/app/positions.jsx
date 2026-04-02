import { useEffect, useState } from "react"
import { View, Text, FlatList, StyleSheet } from "react-native"
import api from "../utils/api"
import { colors } from "../utils/theme"

export default function Positions() {
  const [positions, setPositions] = useState([])

  useEffect(() => {
    api.get("/trades/open")
      .then(data => setPositions(data.positions || []))
      .catch(console.error)
  }, [])

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Open positions</Text>
      <FlatList
        data={positions}
        keyExtractor={(p, i) => p.signal_id || String(i)}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.symbol}>{item.symbol}</Text>
              <Text style={{ color: item.direction === "long" ? colors.teal400 : colors.red400, fontSize: 12 }}>
                {item.direction?.toUpperCase()}
              </Text>
              <Text style={{ color: (item.pnl || 0) >= 0 ? colors.teal400 : colors.red400, fontSize: 13, marginLeft: "auto" }}>
                {item.pnl != null ? `${item.pnl > 0 ? "+" : ""}${item.pnl.toFixed(2)}` : "—"}
              </Text>
            </View>
            <Text style={styles.caption}>Entry: <Text style={styles.mono}>{item.entry?.toFixed(5)}</Text></Text>
            <Text style={styles.caption}>Stop: <Text style={[styles.mono, { color: colors.red400 }]}>{item.stop?.toFixed(5)}</Text></Text>
            <Text style={styles.caption}>Target: <Text style={[styles.mono, { color: colors.teal400 }]}>{item.target?.toFixed(5)}</Text></Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No open positions</Text>}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  card: { backgroundColor: colors.dark800, borderRadius: 12, padding: 14, marginBottom: 10 },
  row: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  symbol: { color: colors.white, fontSize: 15, fontWeight: "500" },
  caption: { color: colors.gray500, fontSize: 12, marginTop: 2 },
  mono: { fontFamily: "monospace" },
  empty: { color: colors.gray600, textAlign: "center", marginTop: 60 },
})
