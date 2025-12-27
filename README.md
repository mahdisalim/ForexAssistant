# 🤖 Forex Analysis Assistant

### AI-Powered Forex Market Analysis & Automated Trading Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 فهرست مطالب

- [معرفی](#-معرفی)
- [ویژگی‌ها](#-ویژگی‌ها)
- [معماری](#-معماری)
- [نصب سریع](#-نصب-سریع)
- [مستندات](#-مستندات)
- [استفاده](#-استفاده)
- [API](#-api)
- [مشارکت](#-مشارکت)
- [لایسنس](#-لایسنس)

---

## 🎯 معرفی

**Forex Analysis Assistant** یک پلتفرم جامع و پیشرفته برای تحلیل و معاملات خودکار فارکس است که با استفاده از هوش مصنوعی (OpenAI GPT-4o-mini) به شما کمک می‌کند تا:

- 📰 اخبار بازار را از **5 منبع معتبر** جمع‌آوری کنید
- 🤖 تحلیل‌های هوشمند و دقیق با **AI** دریافت کنید
- 📊 سیگنال‌های معاملاتی **Buy/Sell** با confidence score تولید کنید
- 📈 چارت‌های TradingView را **خودکار** تحلیل کنید
- 🔄 معاملات را به صورت **کاملاً خودکار** اجرا کنید
- 📧 نوتیفیکیشن‌های **ایمیل** دریافت کنید
- 💼 ربات‌های معاملاتی **سفارشی** بسازید

### 🌟 چرا Forex Analysis Assistant؟

- ✅ **Open Source** - کد کاملاً باز و قابل سفارشی‌سازی
- ✅ **Production Ready** - آماده برای استفاده در محیط واقعی
- ✅ **Docker Support** - نصب آسان با یک دستور
- ✅ **Scalable** - قابل مقیاس‌پذیری برای حجم بالا
- ✅ **Well Documented** - مستندات کامل و جامع
- ✅ **Multi-Language** - پشتیبانی از 14 زبان

---

## ✨ ویژگی‌ها

### 🔍 تحلیل هوشمند بازار

#### 1. جمع‌آوری خودکار اخبار
- **5 منبع معتبر:**
  - 📰 Investing.com - اخبار جهانی
  - 📅 ForexFactory - تقویم اقتصادی
  - 📊 DailyFX - تحلیل تخصصی
  - 📈 FXStreet - تحلیل فنی
  - ⚡ ForexLive - اخبار لحظه‌ای

#### 2. تحلیل با AI
- استفاده از **GPT-4o-mini** برای تحلیل اخبار
- تحلیل **تصویر چارت** با Vision API
- تحلیل **Multi-Timeframe** (چند بازه زمانی همزمان)
- **خلاصه روزانه بازار** به 14 زبان

#### 3. سیگنال‌های معاملاتی
- پیشنهاد **BUY/SELL/HOLD**
- **Confidence Score** (0-100%)
- محاسبه **Stop Loss** و **Take Profit**
- **Risk/Reward Ratio**
- **Entry Zone** دقیق

### 📊 تحلیل چارت

- اسکرین‌شات خودکار از **TradingView**
- تحلیل الگوهای قیمتی
- شناسایی **Support/Resistance**
- تشخیص **Trend** و **Momentum**
- تحلیل **Multi-Timeframe**

### 🤖 معاملات خودکار

#### Trading Robots
- **RSI Bot** - استراتژی RSI
- **Breakout Bot** - شکست سطوح
- **Trend Following** - دنبال کردن روند
- **Mean Reversion** - بازگشت به میانگین
- **Custom Bots** - ربات‌های سفارشی

#### Risk Management
- محاسبه **Position Size** خودکار
- مدیریت **Risk per Trade**
- **Trailing Stop Loss**
- **Partial Take Profit**
- **Max Daily Loss** protection

### 👤 مدیریت کاربران

- ثبت‌نام و ورود با **Email**
- **Token-based Authentication**
- تایید ایمیل با **کد 6 رقمی**
- بازیابی رمز عبور
- **Subscription Plans** (Free/Premium)
- **Admin Panel** کامل

### 📧 سیستم ایمیل

- کد تایید ایمیل
- بازیابی رمز عبور
- تایید خرید اشتراک
- یادآوری انقضای اشتراک (10، 5، 3 روز)
- پیشنهادات تخفیف
- اطلاع‌رسانی رویدادها
- **9 Template** زیبا (فارسی و انگلیسی)

### ⏰ Task Scheduling

- **Celery** برای background tasks
- **Celery Beat** برای scheduled tasks
- چک خودکار انقضای اشتراک
- اسکرپینگ دوره‌ای اخبار
- تحلیل خودکار روزانه

---

## 🏗️ معماری

### Tech Stack

| لایه | تکنولوژی |
|------|----------|
| **Backend** | Django 5.0.1 + FastAPI |
| **API** | Django REST Framework 3.15.2 |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis 7 |
| **Task Queue** | Celery 5.3.6 |
| **AI/LLM** | OpenAI GPT-4o-mini |
| **Scraping** | BeautifulSoup4, httpx, aiohttp |
| **Charts** | Playwright (TradingView) |
| **Email** | Gmail SMTP |
| **Trading** | MetaTrader5 API |
| **Deployment** | Docker + Docker Compose |
| **Web Server** | Gunicorn + Nginx |

### ساختار کلی

```
┌─────────────────────────────────────────────┐
│           Nginx (Load Balancer)             │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
┌────────▼────────┐ ┌───▼──────────┐
│   Django App    │ │  FastAPI     │
│   (Primary)     │ │  (Optional)  │
└────────┬────────┘ └───┬──────────┘
         │               │
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │               │
┌────────▼────────┐ ┌───▼──────────┐
│   PostgreSQL    │ │    Redis     │
└─────────────────┘ └───┬──────────┘
                         │
                ┌────────▼────────┐
                │  Celery Worker  │
                │  + Celery Beat  │
                └────────┬────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   OpenAI API    │            │  News Sources   │
└─────────────────┘            └─────────────────┘
```

**مستندات کامل:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🚀 نصب سریع

### با Docker (پیشنهادی)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/forex-analysis-assistant.git
cd forex-analysis-assistant

# 2. پیکربندی environment
cp .env.example .env
nano .env  # تنظیم OPENAI_API_KEY و سایر متغیرها

# 3. اجرا
cd deploy
docker compose up -d

# 4. Migration
docker compose exec web python manage.py migrate

# 5. ایجاد superuser
docker compose exec web python manage.py createsuperuser

# ✅ آماده است!
# http://localhost:8000
```

### نصب دستی

```bash
# 1. Virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 2. نصب dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Database setup
# نصب PostgreSQL و Redis
# ایجاد database

# 4. پیکربندی
cp .env.example .env
nano .env

# 5. Migration
python manage.py migrate

# 6. اجرا
python manage.py runserver  # Terminal 1
celery -A forex_assistant worker -l info  # Terminal 2
celery -A forex_assistant beat -l info  # Terminal 3
```

**راهنمای کامل:** [SETUP.md](SETUP.md)

---

## 📚 مستندات

### مستندات اصلی

| فایل | توضیحات |
|------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | معماری فنی و ساختار سیستم |
| [SETUP.md](SETUP.md) | راهنمای نصب و راه‌اندازی |
| [API.md](API.md) | مستندات کامل API |
| [DEVELOPMENT.md](DEVELOPMENT.md) | راهنمای توسعه‌دهنده |
| [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) | تحلیل جامع پروژه |
| [PENDING_TASKS.md](PENDING_TASKS.md) | لیست کارهای ناقص |

### مستندات ویژگی‌ها

| فایل | توضیحات |
|------|---------|
| [CHART_ANALYSIS_UPGRADE.md](CHART_ANALYSIS_UPGRADE.md) | سیستم تحلیل چارت |
| [DAILY_SUMMARY_GUIDE.md](DAILY_SUMMARY_GUIDE.md) | خلاصه روزانه بازار |
| [EMAIL_SYSTEM_README.md](EMAIL_SYSTEM_README.md) | سیستم ایمیل |
| [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md) | راهنمای Gmail |

---

## 💻 استفاده

### 1. دسترسی به Dashboard

```
http://localhost:8000/dashboard/
```

### 2. Admin Panel

```
http://localhost:8000/admin/
```

### 3. API Endpoints

#### Authentication
```bash
# ثبت‌نام
POST /api/auth/signup/
{
  "email": "user@example.com",
  "password": "securepass123",
  "name": "John Doe"
}

# ورود
POST /api/auth/signin/
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

#### Analysis
```bash
# تحلیل یک جفت ارز
GET /api/analysis/EURUSD/?timeframe=H4&trading_style=day

# خلاصه روزانه بازار
GET /api/summary/?asset=USD&lang=fa

# لیست جفت ارزها
GET /api/pairs/
```

#### Trading
```bash
# لیست حساب‌های معاملاتی
GET /api/trading-accounts/

# لیست ربات‌ها
GET /api/robots/
```

**مستندات کامل API:** [API.md](API.md)

---

## 📡 API

### نمونه Response - تحلیل جفت ارز

```json
{
  "pair": "EURUSD",
  "timeframe": "H4",
  "analysis": {
    "sentiment": "Bullish",
    "sentiment_score": 75,
    "trend": "uptrend",
    "support_levels": ["1.0850", "1.0820"],
    "resistance_levels": ["1.0920", "1.0950"]
  },
  "recommendation": {
    "recommendation": "BUY",
    "confidence": 75,
    "entry_zone": {"min": "1.0870", "max": "1.0880"},
    "stop_loss": {"price": "1.0840", "pips": 30},
    "take_profit": {"price": "1.0940", "pips": 60},
    "risk_reward_ratio": 2.0
  },
  "generated_at": "2025-12-22T10:30:00Z"
}
```

### نمونه Response - خلاصه روزانه

```json
{
  "articles_count": 45,
  "asset": "USD",
  "lang": "fa",
  "sources": ["Investing.com", "ForexFactory", "DailyFX", "FXStreet", "ForexLive"],
  "summary": "**خلاصه بازار**\n\nدلار آمریکا در معاملات امروز...",
  "generated_at": "2025-12-22T10:30:00Z"
}
```

---

## 🛠️ توسعه

### محیط Development

```bash
# Clone و setup
git clone https://github.com/yourusername/forex-analysis-assistant.git
cd forex-analysis-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# اجرای تست‌ها
python manage.py test

# Code formatting
black .
flake8 .

# Type checking
mypy apps/
```

### ساختار پروژه

```
/srv/
├── apps/                    # Django Applications
│   ├── accounts/            # احراز هویت
│   ├── analysis/            # تحلیل بازار
│   ├── trading/             # معاملات
│   └── scraping/            # اسکرپینگ
├── forex_assistant/         # Django Project
├── scrapers/                # ماژول اسکرپینگ
├── llm/                     # AI/LLM
├── trading/                 # ماژول معاملاتی
├── strategy_bots/           # ربات‌های استراتژیک
└── templates/               # Templates
```

**راهنمای کامل:** [DEVELOPMENT.md](DEVELOPMENT.md)

---

## 🤝 مشارکت

مشارکت شما استقبال می‌شود! لطفاً:

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/amazing-feature`)
3. Commit کنید (`git commit -m 'feat: add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request باز کنید

**راهنمای مشارکت:** [DEVELOPMENT.md](DEVELOPMENT.md)

---

## ⚠️ Disclaimer

> **هشدار مهم:** این نرم‌افزار صرفاً برای **اهداف آموزشی و تحقیقاتی** است.

- معاملات فارکس ریسک بالایی دارد
- عملکرد گذشته تضمینی برای آینده نیست
- همیشه ابتدا با **حساب Demo** تست کنید
- هرگز بیش از توان خود ریسک نکنید
- پیشنهادات AI نباید تنها منبع تصمیم‌گیری باشد
- توسعه‌دهندگان مسئولیتی در قبال ضررهای مالی ندارند

---

## 📄 لایسنس

این پروژه تحت لایسنس [MIT License](LICENSE) منتشر شده است.

---

## 🌟 حمایت از پروژه

اگر این پروژه برایتان مفید بود:

- ⭐ **Star** بدهید
- 🐛 **Bug** گزارش کنید
- 💡 **Feature** پیشنهاد دهید
- 🤝 **Contribute** کنید

---

## 📞 ارتباط

- **Issues:** [GitHub Issues](https://github.com/yourusername/forex-analysis-assistant/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/forex-analysis-assistant/discussions)
- **Email:** support@example.com

---

<div align="center">

### ساخته شده با ❤️ برای جامعه معامله‌گران

**[Documentation](ARCHITECTURE.md)** • **[API Reference](API.md)** • **[Setup Guide](SETUP.md)** • **[Development](DEVELOPMENT.md)**

</div>
