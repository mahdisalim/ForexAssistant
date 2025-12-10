<div align="center">

# 🤖 Forex Analysis Assistant

### AI-Powered Forex Market Analysis & Trading Bot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com)
[![MetaTrader5](https://img.shields.io/badge/MetaTrader-5-orange.svg)](https://www.metatrader5.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#features) | [فارسی](#ویژگی‌ها)

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="60" height="60" alt="Python"/>
&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg" width="60" height="60" alt="FastAPI"/>

</div>

---

## 📋 Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)

---

## ✨ Features

### Phase 1 - Core Analysis
| Feature | Description |
|---------|-------------|
| 📰 **Multi-Source Scraping** | Collects news from 5 trusted sources |
| 🤖 **AI Analysis** | GPT-4o-mini powered market analysis |
| 📊 **Trade Signals** | Buy/Sell recommendations with SL/TP |
| 🌐 **Web Dashboard** | Modern, responsive UI |

**Supported News Sources:**
- Investing.com
- Forex Factory (Calendar + News)
- DailyFX
- FXStreet
- ForexLive

### Phase 2 - Pair Management
- ➕ Add/Remove currency pairs dynamically
- ⚙️ Custom configuration per pair
- 🔍 Auto-detect pairs in news
- 💾 Result caching

### Phase 3 - Algorithmic Trading
- 🔗 MetaTrader 5 integration
- 📈 Risk management & position sizing
- 🤖 Automated trade execution
- 📝 Comprehensive logging & monitoring

---

## � Screenshots

<div align="center">

| Dashboard | Analysis | Trade Signal |
|:---------:|:--------:|:------------:|
| ![Dashboard](https://via.placeholder.com/250x150/1a1a2e/4da6ff?text=Dashboard) | ![Analysis](https://via.placeholder.com/250x150/1a1a2e/10b981?text=Analysis) | ![Signal](https://via.placeholder.com/250x150/1a1a2e/ef4444?text=Signal) |

</div>

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- OpenAI API Key
- MetaTrader 5 (for Phase 3, Windows only)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/forex-analysis-assistant.git
cd forex-analysis-assistant

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Windows VPS (Recommended for Phase 3)

```powershell
# Run as Administrator
.\deploy\install_windows.ps1
```

---

## ⚙️ Configuration

### 1. Create Environment File

```bash
copy .env.example .env
```

### 2. Edit `.env`

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Server
HOST=0.0.0.0
PORT=8000

# MetaTrader 5 (Phase 3)
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server

# Trading Settings
ACCOUNT_BALANCE=10000
RISK_PERCENT=1.0
MIN_CONFIDENCE=60
DEMO_MODE=true
```

### 3. Configure Currency Pairs

Edit `data/pairs.json`:

```json
{
  "EURUSD": {
    "volatility": "medium",
    "default_sl_pips": 30,
    "default_tp_pips": 60,
    "keywords": ["EUR", "USD", "euro", "dollar", "ECB", "Fed"]
  },
  "XAUUSD": {
    "volatility": "high",
    "default_sl_pips": 100,
    "default_tp_pips": 200,
    "keywords": ["gold", "XAU", "precious metal"]
  }
}
```

---

## 📖 Usage

### Web Dashboard

```bash
python main.py
```

Open http://localhost:8000 in your browser.

### Scheduled Analysis

```bash
python scheduler.py
```

### Trading Bot (Phase 3)

```bash
python trading_bot.py
```

### All Services (Windows)

```batch
deploy\start_all.bat
```

---

## 🔌 API Reference

### Pairs Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pairs` | List all pairs |
| `POST` | `/api/pairs` | Add new pair |
| `DELETE` | `/api/pairs/{pair}` | Remove pair |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analysis` | Analyze all pairs |
| `GET` | `/api/analysis/{pair}` | Analyze specific pair |
| `GET` | `/api/summary` | Daily market summary |

### News

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/news` | Get scraped news |
| `POST` | `/api/scrape` | Trigger news scraping |

### Example Response

```json
{
  "pair": "EURUSD",
  "recommendation": "BUY",
  "confidence": 75,
  "timeframe": "H4",
  "stop_loss": {"pips": 30, "description": "Below support"},
  "take_profit": {"pips": 60, "description": "At resistance"},
  "risk_reward_ratio": 2.0,
  "reasoning": "Strong bullish momentum..."
}
```

---

## 📁 Project Structure

```
forex-analysis-assistant/
│
├── 📂 config/
│   └── settings.py           # App configuration
│
├── 📂 scrapers/
│   ├── base_scraper.py       # Abstract scraper class
│   ├── investing_scraper.py  # Investing.com
│   ├── forexfactory_scraper.py
│   ├── dailyfx_scraper.py
│   ├── fxstreet_scraper.py
│   ├── forexlive_scraper.py
│   └── scraper_manager.py    # Orchestrator
│
├── 📂 llm/
│   ├── analyzer.py           # AI analysis engine
│   └── prompts.py            # GPT prompts
│
├── 📂 indicators/
│   ├── risk_manager.py       # Position sizing
│   └── trade_executor.py     # MT5 integration
│
├── 📂 web/
│   ├── app.py                # FastAPI app
│   └── templates/
│       └── index.html        # Dashboard UI
│
├── 📂 deploy/
│   ├── install_windows.ps1   # Windows installer
│   ├── windows_service.py    # Windows service
│   ├── monitor.py            # Health monitor
│   └── start_all.bat         # Startup script
│
├── 📂 data/                   # Stored data
├── 📂 logs/                   # Log files
│
├── main.py                    # Web server entry
├── scheduler.py               # Scheduled tasks
├── trading_bot.py             # Trading bot
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🖥️ Deployment

### Windows VPS (Recommended)

See [deploy/README_VPS.md](deploy/README_VPS.md) for detailed instructions.

```powershell
# Quick deploy
.\deploy\install_windows.ps1

# Start all services
.\deploy\start_all.bat
```

### Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

> **IMPORTANT:** This software is for **educational and research purposes only**.

- Forex trading involves substantial risk of loss
- Past performance does not guarantee future results
- Always test with a **demo account** first
- Never risk more than you can afford to lose
- AI recommendations should not be your sole decision source
- The developers are not responsible for any financial losses

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### ⭐ Star this repo if you find it useful!

Made with ❤️ for the trading community

[Report Bug](https://github.com/yourusername/forex-analysis-assistant/issues) · [Request Feature](https://github.com/yourusername/forex-analysis-assistant/issues)

</div>
