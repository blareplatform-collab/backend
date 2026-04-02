import { useState } from "react"
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native"
import { colors } from "../utils/theme"

export default function Settings() {
  const [lang, setLang] = useState("en")
  const [mode, setMode] = useState("semi")

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Settings</Text>

      <View style={styles.section}>
        <Text style={styles.label}>Language</Text>
        <View style={styles.row}>
          {["en", "es", "ro"].map(l => (
            <TouchableOpacity key={l} onPress={() => setLang(l)}
              style={[styles.chip, lang === l && styles.chipActive]}>
              <Text style={[styles.chipText, lang === l && styles.chipTextActive]}>
                {l.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Trade Mode</Text>
        <View style={styles.row}>
          {[{ key: "semi", label: "Semi-Auto" }, { key: "auto", label: "Full Auto" }].map(({ key, label }) => (
            <TouchableOpacity key={key} onPress={() => setMode(key)}
              style={[styles.chip, mode === key && styles.chipActive]}>
              <Text style={[styles.chipText, mode === key && styles.chipTextActive]}>
                {label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>API Keys</Text>
        <Text style={styles.hint}>Configure via EXPO_PUBLIC_API_URL in .env</Text>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.dark950, padding: 16 },
  title: { color: colors.white, fontSize: 20, fontWeight: "500", marginBottom: 14 },
  section: { backgroundColor: colors.dark800, borderRadius: 12, padding: 14, marginBottom: 10 },
  label: { color: colors.gray300, fontSize: 14, marginBottom: 10 },
  row: { flexDirection: "row", gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, backgroundColor: colors.dark700 },
  chipActive: { backgroundColor: colors.teal800 },
  chipText: { color: colors.gray500, fontSize: 13, fontWeight: "500" },
  chipTextActive: { color: colors.teal200 },
  hint: { color: colors.gray600, fontSize: 12 },
})
