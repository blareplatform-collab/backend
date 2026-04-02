# BLARE — Session 01: Monorepo Scaffold

Version: 1.0.0  
Last updated: 2026-03-29  
Status: Ready to build

---

## Context

Read `BLARE_MASTER.md` and `ARCHITECTURE.md` before starting this session.

BLARE is a multi-market AI trading platform. This session creates the complete project skeleton — every folder, every config file, every dependency installed and verified. By the end of this session the app boots, connects to Firebase, and the FastAPI health endpoint is live on Railway.

---

## Goals

- [ ] Full folder structure created
- [ ] FastAPI running and deployed to Railway
- [ ] React + Vite frontend running locally
- [ ] Electron wrapper booting the frontend
- [ ] Firebase project initialized (Auth + Firestore)
- [ ] All environment variables configured
- [ ] Git repo initialized

---

## Prerequisites

Before starting, have these ready:

1. **Firebase project** — create at console.firebase.google.com
   - Enable Firestore (native mode)
   - Enable Authentication (Email/Password)
   - Generate service account key (Project Settings → Service Accounts)

2. **Railway account** — railway.app
   - New project ready

3. **Binance account** — binance.com
   - API key created (testnet: testnet.binance.vision)

4. **OANDA account** — oanda.com
   - Practice account created
   - API key generated (fxTrade Practice)

5. **Alpha Vantage** — alphavantage.co
   - Free API key claimed

6. **Anthropic API key** — console.anthropic.com

7. **DeepSeek API key** — platform.deepseek.com

---

## Step 1 — Create the monorepo

```bash
mkdir blare
cd blare
git init
```

Create `.gitignore`:
```
# Python
__pycache__/
*.pyc
*.pyo
.env
venv/
*.egg-info/

# Node
node_modules/
dist/
.vite/
*.local

# Electron
out/
release/

# Expo
.expo/
ios/
android/

# Misc
.DS_Store
*.log
```

---

## Step 2 — Backend scaffold

```bash
mkdir -p backend/{config,connectors,engine/patterns,ai,execution,notifications,models,routes}
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### requirements.txt
```
fastapi==0.115.0
uvicorn==0.30.0
python-dotenv==1.0.0
firebase-admin==6.5.0
apscheduler==3.10.4
anthropic==0.40.0
httpx==0.27.0
websockets==13.0
pandas==2.2.0
numpy==1.26.0
python-binance==1.0.19
oandapyV20==0.7.2
```

```bash
pip install -r requirements.txt
```

### backend/config/settings.py
```python
"""
BLARE Settings
Loads all environment variables and exposes them as typed constants.
Never import os.environ directly elsewhere — always import from here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# App
APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", 8000))
IS_DEV = APP_ENV == "development"

# Firebase
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# OANDA
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")

# Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# AI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Risk defaults
DEFAULT_RISK_PCT = float(os.getenv("DEFAULT_RISK_PCT", 1.0))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", 3.0))

# Instruments to watch
CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
FOREX_SYMBOLS = ["EUR_USD", "GBP_USD", "USD_JPY"]
INDICES_SYMBOLS = ["SPX", "NDX", "DAX"]
COMMODITY_SYMBOLS = ["XAU", "WTI"]
```

### backend/config/firebase.py
```python
"""
BLARE Firebase initialization.
Call init_firebase() once at app startup.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from config.settings import (
    FIREBASE_PROJECT_ID,
    FIREBASE_PRIVATE_KEY,
    FIREBASE_CLIENT_EMAIL
)

db = None

def init_firebase():
    """Initialize Firebase Admin SDK and Firestore client."""
    global db
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key": FIREBASE_PRIVATE_KEY,
            "client_email": FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] Connected successfully")
        return db
    except Exception as e:
        print(f"[Firebase] Connection failed: {e}")
        raise

def get_db():
    """Returns the Firestore client. Raises if not initialized."""
    if db is None:
        raise RuntimeError("Firebase not initialized. Call init_firebase() first.")
    return db
```

### backend/main.py
```python
"""
BLARE — FastAPI main entry point.
Initializes all services and mounts all routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.firebase import init_firebase
from config.settings import APP_ENV
from routes import signals, trades, strategies, profiles, backtest

app = FastAPI(
    title="BLARE API",
    description="Bot-powered Liquidity Analysis & Risk Execution",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    print(f"[BLARE] Starting in {APP_ENV} mode")
    init_firebase()
    print("[BLARE] All systems ready")

@app.get("/health")
async def health():
    return {"status": "ok", "app": "BLARE", "version": "1.0.0"}

app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
```

### Stub route files (create each):

`backend/routes/signals.py`:
```python
"""BLARE signals routes."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def get_signals():
    return {"signals": [], "message": "Signals endpoint ready"}
```

Same pattern for `trades.py`, `strategies.py`, `profiles.py`, `backtest.py`.

---

## Step 3 — Frontend scaffold

```bash
cd ..
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite zustand axios i18next react-i18next
npm install lightweight-charts
```

### frontend/src/App.jsx
```jsx
import { useState } from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-5xl font-medium text-teal-400 tracking-tight">BLARE</h1>
        <p className="text-gray-500 mt-2 text-sm tracking-widest">
          BOT-POWERED LIQUIDITY ANALYSIS & RISK EXECUTION
        </p>
        <p className="text-gray-600 mt-6 text-xs">Session 01 — scaffold complete</p>
      </div>
    </div>
  )
}

export default App
```

### frontend/src/utils/api.js
```javascript
/**
 * BLARE API client.
 * All backend calls go through this axios instance.
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

api.interceptors.response.use(
  res => res.data,
  err => {
    console.error('[BLARE API Error]', err.message)
    return Promise.reject(err)
  }
)

export default api
```

### frontend/.env
```
VITE_API_URL=http://localhost:8000
```

---

## Step 4 — Electron scaffold

```bash
cd ..
mkdir desktop && cd desktop
npm init -y
npm install --save-dev electron electron-builder
```

### desktop/electron.js
```javascript
/**
 * BLARE Desktop — Electron main process.
 * Loads the React frontend in a BrowserWindow.
 */
const { app, BrowserWindow, Notification } = require('electron')
const path = require('path')

const isDev = process.env.NODE_ENV === 'development'
const FRONTEND_URL = isDev
  ? 'http://localhost:5173'
  : `file://${path.join(__dirname, '../frontend/dist/index.html')}`

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#030a09',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  win.loadURL(FRONTEND_URL)
  if (isDev) win.webContents.openDevTools()
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
```

### desktop/preload.js
```javascript
/**
 * BLARE Desktop — Electron preload script.
 * Exposes safe IPC methods to the renderer.
 */
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('blare', {
  notify: (title, body) => ipcRenderer.invoke('notify', { title, body }),
  getVersion: () => ipcRenderer.invoke('get-version'),
})
```

### desktop/package.json — add these fields:
```json
{
  "main": "electron.js",
  "scripts": {
    "dev": "NODE_ENV=development electron .",
    "build": "electron-builder"
  }
}
```

---

## Step 5 — Mobile scaffold

```bash
cd ..
npx create-expo-app mobile --template blank
cd mobile
npx expo install expo-router expo-notifications @react-native-firebase/app
```

### mobile/app/index.jsx
```jsx
import { View, Text, StyleSheet } from 'react-native'

export default function Home() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>BLARE</Text>
      <Text style={styles.sub}>Mobile scaffold ready</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#030a09',
    alignItems: 'center', justifyContent: 'center' },
  title: { color: '#1D9E75', fontSize: 42, fontWeight: '500' },
  sub: { color: '#444', marginTop: 8, fontSize: 12, letterSpacing: 2 },
})
```

---

## Step 6 — Environment file

Create `.env.example` in the root:
```bash
# BLARE Environment Variables
# Copy to backend/.env and fill in your values

APP_ENV=development
APP_PORT=8000

FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com

BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=true

OANDA_API_KEY=
OANDA_ACCOUNT_ID=
OANDA_ENVIRONMENT=practice

ALPHA_VANTAGE_API_KEY=

ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=

DEFAULT_RISK_PCT=1.0
MAX_DAILY_LOSS_PCT=3.0
```

---

## Step 7 — Deploy backend to Railway

```bash
cd backend
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port $PORT" > Procfile
```

In Railway dashboard:
1. New project → Deploy from GitHub repo
2. Set root directory to `/backend`
3. Add all env vars from `.env`
4. Deploy → verify `GET /health` returns `{"status":"ok"}`

---

## Step 8 — Verify everything

Checklist:
- [ ] `cd backend && uvicorn main:app --reload` → `http://localhost:8000/health` returns OK
- [ ] `cd frontend && npm run dev` → `http://localhost:5173` shows BLARE splash
- [ ] `cd desktop && npm run dev` → Electron window opens with frontend
- [ ] Railway deployment live and `/health` responding
- [ ] Firebase console shows project connected (check Firestore + Auth)
- [ ] No hardcoded keys anywhere in source code

---

## Session 01 Complete

Commit message: `feat: session 01 — monorepo scaffold complete`

Next: **Session 02 — Data Pipeline**
