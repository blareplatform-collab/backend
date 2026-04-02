import { useState } from "react"
import { auth } from "../config/firebase"
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
} from "firebase/auth"
import { useNavigate } from "react-router-dom"

export default function Login() {
  const [mode, setMode] = useState("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async () => {
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      if (mode === "login") {
        await signInWithEmailAndPassword(auth, email, password)
        navigate("/")
      } else if (mode === "signup") {
        await createUserWithEmailAndPassword(auth, email, password)
        navigate("/")
      } else if (mode === "reset") {
        await sendPasswordResetEmail(auth, email)
        setSuccess("Password reset email sent. Check your inbox.")
      }
    } catch (e) {
      setError(e.message.replace("Firebase: ", "").replace(/\(auth.*\)/, ""))
    }
    setLoading(false)
  }

  const handleGoogle = async () => {
    try {
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
      navigate("/")
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex justify-center gap-1 items-end h-8 mb-3">
            {[2, 3, 4, 5].map((h, i) => (
              <div key={i} className="w-2 rounded-sm bg-teal-400"
                style={{ height: `${h * 6}px`, opacity: 0.5 + i * 0.15 }} />
            ))}
          </div>
          <h1 className="text-white text-3xl font-medium tracking-tight">BLARE</h1>
          <p className="text-gray-600 text-xs mt-1 tracking-widest">
            {mode === "login" ? "SIGN IN" : mode === "signup" ? "CREATE ACCOUNT" : "RESET PASSWORD"}
          </p>
        </div>

        <div className="bg-dark-800 rounded-2xl p-6 border border-dark-700">
          <div className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full bg-dark-900 text-white text-sm rounded-xl border border-dark-700 px-4 py-3 outline-none focus:border-teal-600 placeholder-gray-600 transition-colors"
            />
            {mode !== "reset" && (
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSubmit()}
                className="w-full bg-dark-900 text-white text-sm rounded-xl border border-dark-700 px-4 py-3 outline-none focus:border-teal-600 placeholder-gray-600 transition-colors"
              />
            )}
          </div>

          {error && <p className="text-red-400 text-xs mt-3 text-center">{error}</p>}
          {success && <p className="text-teal-400 text-xs mt-3 text-center">{success}</p>}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full mt-4 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white rounded-xl py-3 text-sm font-medium transition-colors">
            {loading ? "..." : mode === "login" ? "Sign in" : mode === "signup" ? "Create account" : "Send reset email"}
          </button>

          {mode !== "reset" && (
            <>
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-dark-700" />
                <span className="text-gray-600 text-xs">or</span>
                <div className="flex-1 h-px bg-dark-700" />
              </div>
              <button
                onClick={handleGoogle}
                className="w-full bg-dark-900 hover:bg-dark-700 text-white rounded-xl py-3 text-sm border border-dark-700 transition-colors">
                Continue with Google
              </button>
            </>
          )}

          <div className="flex justify-between mt-4">
            {mode === "login" && (
              <>
                <button onClick={() => setMode("signup")}
                  className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                  Create account
                </button>
                <button onClick={() => setMode("reset")}
                  className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                  Forgot password?
                </button>
              </>
            )}
            {(mode === "signup" || mode === "reset") && (
              <button onClick={() => setMode("login")}
                className="text-gray-500 hover:text-teal-400 text-xs transition-colors">
                Back to sign in
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
