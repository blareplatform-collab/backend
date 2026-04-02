import { View, Text, TouchableOpacity, StyleSheet } from "react-native"
import { colors } from "../utils/theme"
import { useSignalStore } from "../store/signalStore"

const confidenceColor = (score) => {
  if (score >= 86) return colors.teal400
  if (score >= 71) return colors.teal200
  if (score >= 51) return colors.yellow400
  return colors.gray500
}

export default function SignalCard({ signal, tradeMode = "semi" }) {
  const { approveSignal, rejectSignal } = useSignalStore()
  const isLong = signal.direction === "long"
  const isPending = signal.status === "pending"

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.row}>
          <Text style={styles.symbol}>{signal.symbol}</Text>
          <View style={[styles.badge, { backgroundColor: isLong ? "#085041" : "#450a0a" }]}>
            <Text style={{ color: isLong ? colors.teal200 : "#fca5a5", fontSize: 11, fontWeight: "600" }}>
              {isLong ? "LONG" : "SHORT"}
            </Text>
          </View>
          <Text style={styles.caption}>{signal.timeframe}</Text>
        </View>
        <Text style={{ color: confidenceColor(signal.confidence), fontSize: 13, fontWeight: "500" }}>
          {signal.confidence}/100
        </Text>
      </View>

      <View style={[styles.row, { marginTop: 10 }]}>
        {[
          { label: "Entry", value: signal.entry, color: colors.white },
          { label: "Stop", value: signal.stop, color: colors.red400 },
          { label: "Target", value: signal.target, color: colors.teal400 },
        ].map(({ label, value, color }) => (
          <View key={label} style={styles.levelBox}>
            <Text style={styles.caption}>{label}</Text>
            <Text style={[styles.mono, { color }]}>{Number(value).toFixed(5)}</Text>
          </View>
        ))}
      </View>

      <View style={[styles.row, { marginTop: 8 }]}>
        <Text style={styles.caption}>R:R </Text>
        <Text style={{ color: colors.teal400, fontSize: 13 }}>{signal.rr}:1</Text>
        <Text style={[styles.caption, { marginLeft: 16 }]}>Size </Text>
        <Text style={{ color: colors.white, fontSize: 13 }}>{signal.position_size_pct}%</Text>
      </View>

      {signal.ai_note ? (
        <View style={styles.aiBox}>
          <Text style={{ color: colors.teal800, fontSize: 11, marginBottom: 4 }}>AI Analysis</Text>
          <Text style={{ color: colors.gray300, fontSize: 13, lineHeight: 18 }}>{signal.ai_note}</Text>
        </View>
      ) : null}

      {tradeMode === "semi" && isPending && (
        <View style={[styles.row, { marginTop: 12, gap: 8 }]}>
          <TouchableOpacity style={[styles.btn, { backgroundColor: colors.teal800 }]}
            onPress={() => approveSignal(signal.id)}>
            <Text style={{ color: colors.teal200, fontWeight: "500" }}>Approve</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.btn, { backgroundColor: colors.dark700 }]}
            onPress={() => rejectSignal(signal.id)}>
            <Text style={{ color: colors.gray500, fontWeight: "500" }}>Reject</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.dark800, borderRadius: 12,
    borderWidth: 1, borderColor: colors.dark700, padding: 14, marginBottom: 10,
  },
  row: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 8 },
  symbol: { color: colors.white, fontSize: 16, fontWeight: "500" },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  caption: { color: colors.gray500, fontSize: 12 },
  mono: { fontFamily: "monospace", fontSize: 12 },
  levelBox: { flex: 1, backgroundColor: colors.dark900, borderRadius: 8, padding: 8, alignItems: "center" },
  aiBox: { marginTop: 10, backgroundColor: colors.dark900, borderRadius: 8, borderWidth: 1, borderColor: "#142b26", padding: 10 },
  btn: { flex: 1, padding: 10, borderRadius: 8, alignItems: "center" },
})
