# 🏗️ معماری فنی پروژه Forex Analysis Assistant

**نسخه:** 2.0  
**تاریخ:** 2025-12-22

---

## 📋 فهرست مطالب

1. [نمای کلی](#نمای-کلی)
2. [معماری سیستم](#معماری-سیستم)
3. [لایه‌های برنامه](#لایه‌های-برنامه)
4. [مدل‌های دیتابیس](#مدل‌های-دیتابیس)
5. [جریان داده](#جریان-داده)
6. [سرویس‌های خارجی](#سرویس‌های-خارجی)
7. [امنیت](#امنیت)
8. [مقیاس‌پذیری](#مقیاس‌پذیری)

---

## 🎯 نمای کلی

Forex Analysis Assistant یک پلتفرم جامع برای تحلیل و معاملات خودکار فارکس است که از هوش مصنوعی استفاده می‌کند.

### اهداف معماری:
- **Modularity**: ماژول‌های مستقل و قابل تعویض
- **Scalability**: قابلیت مقیاس‌پذیری افقی
- **Maintainability**: کد تمیز و قابل نگهداری
- **Reliability**: سیستم پایدار با error handling مناسب

---

## 🏛️ معماری سیستم

### معماری فعلی (Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                      (Nginx - Optional)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   Django App    │            │  FastAPI App    │
│   (Primary)     │            │  (Legacy/API)   │
│                 │            │                 │
│ - REST API      │            │ - Web UI        │
│ - Admin Panel   │            │ - WebSocket     │
│ - Auth          │            │ - Real-time     │
└────────┬────────┘            └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   PostgreSQL    │            │      Redis      │
│   (Database)    │            │   (Cache/Queue) │
└─────────────────┘            └─────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                ┌────────▼────────┐
                │  Celery Worker  │
                │  + Celery Beat  │
                │                 │
                │ - Async Tasks   │
                │ - Scheduling    │
                └────────┬────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   OpenAI API    │            │  News Sources   │
│   (GPT-4o-mini) │            │  (5 Scrapers)   │
└─────────────────┘            └─────────────────┘
```

---

## 📚 لایه‌های برنامه

### 1. Presentation Layer (رابط کاربری)

#### Django Templates
```
/srv/templates/
├── landing.html          # صفحه اصلی
├── index.html            # داشبورد
├── signin.html           # ورود
├── signup.html           # ثبت‌نام
├── pricing.html          # قیمت‌گذاری
└── emails/               # قالب‌های ایمیل
    ├── verification_fa.html
    ├── password_reset_fa.html
    └── ...
```

#### Static Files
```
/srv/web/static/
├── css/
├── js/
├── images/
└── locales/              # فایل‌های ترجمه
```

---

### 2. Application Layer (منطق برنامه)

#### Django Apps

##### A. Accounts App (`apps/accounts/`)
**مسئولیت:** مدیریت کاربران و احراز هویت

**Components:**
```python
models.py:
  - User (Custom User Model)
  - AuthToken (Token-based Auth)
  - EmailVerification (کدهای تایید)
  - PasswordResetToken (بازیابی رمز)
  - EmailNotification (ردیابی ایمیل‌ها)

views.py:
  - sign_up() - ثبت‌نام
  - sign_in() - ورود
  - logout() - خروج
  - get_current_user() - اطلاعات کاربر

email_service.py:
  - EmailService class
  - 7 متد برای انواع ایمیل‌ها

tasks.py (Celery):
  - check_subscription_expiry()
  - send_verification_email_task()
  - bulk_send_discount_offer()
```

**Database Schema:**
```sql
User:
  - id (PK)
  - email (UNIQUE)
  - password (hashed)
  - subscription_plan (free/premium)
  - subscription_expires
  - is_active

AuthToken:
  - id (PK)
  - user_id (FK)
  - token (UNIQUE)
  - created_at
  - expires_at
  - is_active

EmailVerification:
  - id (PK)
  - user_id (FK)
  - code (6 digits)
  - created_at
  - expires_at (15 min)
  - is_used
```

---

##### B. Analysis App (`apps/analysis/`)
**مسئولیت:** تحلیل بازار و تولید سیگنال

**Components:**
```python
models.py:
  - CurrencyPair (جفت ارزها)
  - MarketAnalysis (تحلیل‌های ذخیره شده)
  - DailySummary (خلاصه روزانه)
  - ChartAnalysis (تحلیل چارت)

services.py:
  - AnalysisService class
  - auto_chart_analysis() - تحلیل خودکار
  - generate_daily_summary() - خلاصه روزانه
  - Multi-timeframe analysis

chart_service.py:
  - TradingViewChartService
  - capture_chart_screenshot() - اسکرین‌شات چارت
  - capture_multi_timeframe_charts()

views.py:
  - list_pairs() - لیست جفت ارزها
  - analyze_pair() - تحلیل یک جفت ارز
  - daily_summary() - خلاصه روزانه
  - multi_timeframe_analysis()
```

**Database Schema:**
```sql
CurrencyPair:
  - id (PK)
  - symbol (UNIQUE) - e.g., EURUSD
  - tradingview_symbol - e.g., FX:EURUSD
  - volatility (low/medium/high)
  - default_sl_pips
  - default_tp_pips
  - keywords (JSON)
  - is_active

MarketAnalysis:
  - id (PK)
  - pair_id (FK)
  - timeframe
  - sentiment (bullish/bearish/neutral)
  - sentiment_score (0-100)
  - recommendation (BUY/SELL/HOLD)
  - confidence (0-100)
  - analysis_text
  - generated_at

ChartAnalysis:
  - id (PK)
  - pair_id (FK)
  - timeframe
  - chart_image (base64)
  - analysis (JSON)
  - generated_at
```

---

##### C. Trading App (`apps/trading/`)
**مسئولیت:** مدیریت حساب‌های معاملاتی و ربات‌ها

**Components:**
```python
models.py:
  - TradingAccount (حساب‌های کاربر)
  - TradingRobot (ربات‌های فعال)
  - Trade (معاملات انجام شده)

views.py:
  - list_trading_accounts()
  - add_trading_account()
  - get_available_robots()
  - create_robot()
  - list_trades()
```

**⚠️ وضعیت:** ناقص - نیاز به ادغام با `/srv/trading/` و `/srv/strategy_bots/`

---

##### D. Scraping App (`apps/scraping/`)
**مسئولیت:** جمع‌آوری اخبار از منابع مختلف

**Components:**
```python
models.py:
  - NewsArticle (اخبار ذخیره شده)
  - ScrapeLog (لاگ اسکرپینگ)

tasks.py (Celery):
  - trigger_scrape_task()
  - daily_analysis_task()
```

**⚠️ وضعیت:** ناقص - نیاز به ادغام با `/srv/scrapers/`

---

### 3. Business Logic Layer (منطق کسب‌وکار)

#### Independent Modules (ماژول‌های مستقل)

##### A. Scrapers (`/srv/scrapers/`)
**مسئولیت:** جمع‌آوری اخبار از 5 منبع

```python
base_scraper.py:
  - BaseScraper (کلاس پایه)
  - NewsArticle (dataclass)

investing_scraper.py:
  - InvestingScraper
  - scrape() -> List[NewsArticle]

forexfactory_scraper.py:
  - ForexFactoryScraper
  - scrape_news()
  - scrape_calendar()

dailyfx_scraper.py:
  - DailyFXScraper

fxstreet_scraper.py:
  - FXStreetScraper

forexlive_scraper.py:
  - ForexLiveScraper

scraper_manager.py:
  - ScraperManager
  - scrape_all() - اجرای همه scrapers
  - filter_by_pairs()
  - save_to_file()
```

**منابع خبری:**
1. Investing.com - اخبار جهانی
2. ForexFactory - تقویم اقتصادی
3. DailyFX - تحلیل تخصصی
4. FXStreet - تحلیل فنی
5. ForexLive - اخبار لحظه‌ای

---

##### B. LLM Analyzer (`/srv/llm/`)
**مسئولیت:** تحلیل هوشمند با AI

```python
analyzer.py (39,002 خط):
  - ForexAnalyzer
  - analyze_pair() - تحلیل یک جفت ارز
  - get_trade_recommendation() - پیشنهاد معامله
  - analyze_news() - تحلیل اخبار
  - generate_daily_summary() - خلاصه روزانه

chart_analyzer.py:
  - ChartImageAnalyzer
  - analyze_chart_image() - تحلیل تصویر چارت
  - analyze_multi_timeframe_charts()

prompts.py:
  - تمام پرامپت‌های GPT
  - ANALYSIS_PROMPT
  - RECOMMENDATION_PROMPT
  - SUMMARY_PROMPT
```

**AI Workflow:**
```
News Articles → ForexAnalyzer → GPT-4o-mini → Analysis
Chart Image → ChartImageAnalyzer → GPT-4o-mini Vision → Chart Analysis
Multi-TF Charts → analyze_multi_timeframe → Comprehensive Analysis
```

---

##### C. Trading Modules (`/srv/trading/`)
**مسئولیت:** منطق معاملاتی پیشرفته

```python
robot_manager.py (15,518 خط):
  - RobotManager
  - مدیریت ربات‌های معاملاتی

unified_robots.py (15,808 خط):
  - UnifiedTradingRobot
  - ربات‌های یکپارچه

support_resistance.py (34,910 خط):
  - محاسبات Support/Resistance
  - Pivot Points
  - Fibonacci Levels

advanced_sl_strategies.py (39,100 خط):
  - استراتژی‌های Stop Loss پیشرفته

advanced_tp_strategies.py (30,809 خط):
  - استراتژی‌های Take Profit پیشرفته

pattern_detection.py:
  - تشخیص الگوهای قیمتی

market_sessions.py:
  - مدیریت سشن‌های بازار
```

---

##### D. Strategy Bots (`/srv/strategy_bots/`)
**مسئولیت:** ربات‌های استراتژیک

```python
base_bot.py (11,774 خط):
  - BaseTradingBot
  - کلاس پایه برای همه ربات‌ها

rsi_bot.py (21,550 خط):
  - RSITradingBot
  - استراتژی RSI

sl_strategies/:
  - 6 استراتژی مختلف Stop Loss

tp_strategies/:
  - 6 استراتژی مختلف Take Profit
```

---

##### E. Indicators (`/srv/indicators/`)
**مسئولیت:** ابزارهای معاملاتی

```python
risk_manager.py:
  - RiskManager
  - محاسبه حجم معامله
  - مدیریت ریسک

trade_executor.py:
  - TradeExecutor
  - اتصال به MetaTrader 5
  - اجرای معاملات
```

---

### 4. Data Layer (لایه داده)

#### PostgreSQL Database
```
forex_assistant (database)
├── accounts_user
├── accounts_authtoken
├── accounts_emailverification
├── accounts_passwordresettoken
├── accounts_emailnotification
├── analysis_currencypair
├── analysis_marketanalysis
├── analysis_dailysummary
├── analysis_chartanalysis
├── trading_tradingaccount
├── trading_tradingrobot
├── trading_trade
├── scraping_newsarticle
└── scraping_scrapelog
```

#### Redis
```
Database 0: Cache
Database 1: Celery Broker
Database 2: Celery Results
```

#### File Storage
```
/srv/data/
├── pairs.json           # پیکربندی جفت ارزها
├── news_*.json          # اخبار ذخیره شده
├── daily_report_*.json  # گزارش‌های روزانه
└── charts/              # تصاویر چارت
```

---

## 🔄 جریان داده

### 1. جریان ثبت‌نام و ورود

```
User → POST /api/signup
  ↓
SignUpSerializer.validate()
  ↓
User.objects.create()
  ↓
AuthToken.generate_token()
  ↓
EmailService.send_verification_email()
  ↓
Celery Task (async)
  ↓
Gmail SMTP
  ↓
Response: {user, token}
```

### 2. جریان تحلیل بازار

```
User → GET /api/analysis/{pair}
  ↓
AnalysisService.auto_chart_analysis()
  ↓
┌─────────────────┬─────────────────┐
│                 │                 │
TradingViewChartService  ScraperManager
│                 │                 │
capture_screenshot()  scrape_all()
│                 │                 │
└─────────────────┴─────────────────┘
          ↓
    ForexAnalyzer
          ↓
    OpenAI API (GPT-4o-mini)
          ↓
    Analysis + Recommendation
          ↓
    Save to Database
          ↓
    Response: {analysis, recommendation}
```

### 3. جریان خلاصه روزانه

```
Celery Beat (Daily 9:00 AM)
  ↓
check_subscription_expiry()
  ↓
Query Users (subscription_expires in 10/5/3 days)
  ↓
For each user:
  ↓
  EmailService.send_expiry_warning()
  ↓
  Celery Task (async)
  ↓
  Gmail SMTP
```

### 4. جریان معامله خودکار (Trading Bot)

```
TradingBot.run()
  ↓
ScraperManager.scrape_all()
  ↓
ForexAnalyzer.analyze_pair()
  ↓
Check confidence > MIN_CONFIDENCE
  ↓
RiskManager.calculate_position_size()
  ↓
TradeExecutor.place_order()
  ↓
MetaTrader 5 API
  ↓
Save Trade to Database
  ↓
Log to file
```

---

## 🔌 سرویس‌های خارجی

### 1. OpenAI API
```python
Endpoint: https://api.openai.com/v1/chat/completions
Model: gpt-4o-mini
Usage:
  - تحلیل اخبار
  - تولید سیگنال معاملاتی
  - خلاصه روزانه بازار
  - تحلیل تصویر چارت (Vision API)

Rate Limits:
  - 10,000 requests/day (بسته به plan)
  - Token limits per request
```

### 2. TradingView
```python
Usage:
  - دریافت چارت‌های real-time
  - Playwright automation
  - Screenshot capture

URL Pattern:
  https://www.tradingview.com/chart/?symbol={symbol}&interval={timeframe}
```

### 3. News Sources APIs
```python
1. Investing.com
   - Web scraping (BeautifulSoup)
   - Rate limit: 1 req/sec

2. ForexFactory
   - Web scraping
   - Calendar API

3. DailyFX
   - RSS Feed + Web scraping

4. FXStreet
   - Web scraping

5. ForexLive
   - Web scraping
```

### 4. MetaTrader 5
```python
Library: MetaTrader5
Connection:
  - Login credentials
  - Server address
  - Demo/Live account

Functions:
  - initialize()
  - login()
  - symbol_info()
  - order_send()
  - positions_get()
```

### 5. Gmail SMTP
```python
Host: smtp.gmail.com
Port: 587
TLS: True
Authentication: App Password

Usage:
  - ارسال کد تایید
  - بازیابی رمز عبور
  - نوتیفیکیشن‌ها
```

---

## 🔐 امنیت

### Authentication & Authorization

```python
# Token-based Authentication
class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = get_token_from_header(request)
        auth_token = AuthToken.objects.get(token=token)
        if auth_token.is_valid():
            return (auth_token.user, auth_token)
        raise AuthenticationFailed()
```

### Password Security
- Django's PBKDF2 hashing
- Minimum 8 characters
- Password reset tokens expire in 1 hour

### API Key Security
```python
# Encryption for sensitive data
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY)

encrypted_password = cipher.encrypt(password.encode())
```

### CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com",
]
```

### Rate Limiting
```python
# TODO: Implement with Django-ratelimit
@ratelimit(key='ip', rate='100/h')
def api_endpoint(request):
    pass
```

---

## 📈 مقیاس‌پذیری

### Horizontal Scaling

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ App 1 │ │ App 2 │ ... App N
└───┬───┘ └──┬────┘
    │         │
    └────┬────┘
         │
┌────────▼────────┐
│   PostgreSQL    │
│   (Primary)     │
└────────┬────────┘
         │
┌────────▼────────┐
│   PostgreSQL    │
│   (Replica)     │
└─────────────────┘
```

### Caching Strategy

```python
# Redis Caching
from django.core.cache import cache

def get_analysis(pair):
    cache_key = f'analysis:{pair}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    analysis = generate_analysis(pair)
    cache.set(cache_key, analysis, timeout=3600)  # 1 hour
    return analysis
```

### Celery Workers

```
Celery Worker 1: Email tasks
Celery Worker 2: Scraping tasks
Celery Worker 3: Analysis tasks
Celery Beat: Scheduled tasks
```

### Database Optimization

```python
# Query optimization
users = User.objects.select_related('subscription').prefetch_related('analyses')

# Indexing
class Meta:
    indexes = [
        models.Index(fields=['email']),
        models.Index(fields=['subscription_expires']),
    ]
```

---

## 🔧 تکنولوژی‌های استفاده شده

| لایه | تکنولوژی |
|------|----------|
| **Backend Framework** | Django 5.0.1 + FastAPI |
| **API** | Django REST Framework 3.15.2 |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis 7 |
| **Task Queue** | Celery 5.3.6 |
| **AI/LLM** | OpenAI GPT-4o-mini |
| **Web Scraping** | BeautifulSoup4, httpx |
| **Browser Automation** | Playwright |
| **Email** | Gmail SMTP |
| **Trading** | MetaTrader5 |
| **Deployment** | Docker + Docker Compose |
| **Web Server** | Gunicorn + Nginx |

---

## 📊 Performance Metrics

### Target Performance:
- API Response Time: < 200ms (cached)
- Analysis Generation: < 30s
- Scraping All Sources: < 60s
- Database Query Time: < 50ms
- Concurrent Users: 100+

### Monitoring:
```python
# TODO: Implement
- Sentry for error tracking
- Prometheus for metrics
- Grafana for visualization
```

---

**یادداشت:** این معماری در حال تکامل است و با توسعه پروژه به‌روز می‌شود.
