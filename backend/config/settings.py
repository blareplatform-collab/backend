from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000

    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

    # Connectors
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    oanda_api_key: str = ""
    oanda_account_id: str = ""
    oanda_environment: str = "practice"

    alpha_vantage_api_key: str = ""

    # AI
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""

    # Risk Defaults
    default_risk_pct: float = 1.0
    max_daily_loss_pct: float = 3.0

    # Trading mode
    auto_trade_mode: str = "semi"  # "semi" or "auto"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Module-level constants for direct import by connectors
APP_ENV = settings.app_env
APP_PORT = settings.app_port
IS_DEV = APP_ENV == "development"

FIREBASE_PROJECT_ID = settings.firebase_project_id
FIREBASE_PRIVATE_KEY = settings.firebase_private_key.replace("\\n", "\n")
FIREBASE_CLIENT_EMAIL = settings.firebase_client_email

BINANCE_API_KEY = settings.binance_api_key
BINANCE_API_SECRET = settings.binance_api_secret
BINANCE_TESTNET = settings.binance_testnet

OANDA_API_KEY = settings.oanda_api_key
OANDA_ACCOUNT_ID = settings.oanda_account_id
OANDA_ENVIRONMENT = settings.oanda_environment

ALPHA_VANTAGE_API_KEY = settings.alpha_vantage_api_key

ANTHROPIC_API_KEY = settings.anthropic_api_key
DEEPSEEK_API_KEY = settings.deepseek_api_key

DEFAULT_RISK_PCT = settings.default_risk_pct
MAX_DAILY_LOSS_PCT = settings.max_daily_loss_pct

AUTO_TRADE_MODE = settings.auto_trade_mode  # "semi" or "auto"

CRYPTO_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
]
FOREX_SYMBOLS = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD", "USD_CHF", "NZD_USD"]
INDICES_SYMBOLS = ["SPX", "NDX", "DAX"]
COMMODITY_SYMBOLS = ["XAU", "WTI"]
