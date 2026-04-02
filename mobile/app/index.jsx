import { useEffect } from "react"
import { View, FlatList, Text, StyleSheet, RefreshControl } from "react-native"
import { useSignalStore } from "../store/signalStore"
import SignalCard from "../components/SignalCard"
import { colors } from "../utils/theme"

export default function Signals() {
  const { signals, loading, fetchSignals } = useSignalStore()

  useEffect(() => {
    fetchSignals()
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live signals</Text>
      <FlatList
        data={signals}
        keyExtractor={s => s.id}
        renderItem={({ item }) => <SignalCard signal={item} tradeMode="semi" />}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={fetchSignals} tintColor={colors.teal400} />
        }
        ListEmptyComponent={<Text style={styles.empty}>Scanning markets...</Text>}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  empty: { color: colors.gray600, textAlign: "center", marginTop: 60 },
})
