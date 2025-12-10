"""
Application Settings and Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Scraping Configuration
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 60))
MAX_NEWS_AGE_HOURS = int(os.getenv("MAX_NEWS_AGE_HOURS", 24))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Default currency pairs
DEFAULT_PAIRS = ["EURUSD", "XAUUSD", "GBPUSD", "USDJPY"]

# News sources configuration
NEWS_SOURCES = {
    "investing": {
        "name": "Investing.com",
        "base_url": "https://www.investing.com",
        "enabled": True
    },
    "forexfactory": {
        "name": "Forex Factory",
        "base_url": "https://www.forexfactory.com",
        "enabled": True
    },
    "dailyfx": {
        "name": "DailyFX",
        "base_url": "https://www.dailyfx.com",
        "enabled": True
    },
    "fxstreet": {
        "name": "FXStreet",
        "base_url": "https://www.fxstreet.com",
        "enabled": True
    },
    "forexlive": {
        "name": "ForexLive",
        "base_url": "https://www.forexlive.com",
        "enabled": True
    }
}

# Pair-specific configurations
PAIR_CONFIGS = {
    "EURUSD": {
        "volatility": "medium",
        "default_sl_pips": 30,
        "default_tp_pips": 60,
        "keywords": ["EUR", "USD", "euro", "dollar", "ECB", "Fed", "Federal Reserve"]
    },
    "XAUUSD": {
        "volatility": "high",
        "default_sl_pips": 100,
        "default_tp_pips": 200,
        "keywords": ["gold", "XAU", "precious metal", "safe haven", "inflation"]
    },
    "GBPUSD": {
        "volatility": "high",
        "default_sl_pips": 40,
        "default_tp_pips": 80,
        "keywords": ["GBP", "pound", "sterling", "BOE", "Bank of England"]
    },
    "USDJPY": {
        "volatility": "medium",
        "default_sl_pips": 35,
        "default_tp_pips": 70,
        "keywords": ["JPY", "yen", "BOJ", "Bank of Japan", "Japan"]
    }
}
