# 🔍 تحلیل جامع پروژه Forex Analysis Assistant

**تاریخ تحلیل:** 2025-12-22  
**وضعیت:** در حال بازسازی و مستندسازی

---

## 📊 خلاصه اجرایی

این پروژه یک سیستم **تحلیل و معاملات خودکار فارکس** است که با استفاده از هوش مصنوعی (OpenAI GPT-4o-mini) اخبار بازار را تحلیل کرده و سیگنال‌های معاملاتی تولید می‌کند.

### 🎯 هدف اصلی پروژه
ارائه یک پلتفرم جامع برای:
1. جمع‌آوری خودکار اخبار فارکس از 5 منبع معتبر
2. تحلیل هوشمند اخبار با AI
3. تولید سیگنال‌های معاملاتی (Buy/Sell)
4. اجرای خودکار معاملات از طریق MetaTrader 5
5. مدیریت ریسک و پوزیشن‌ها
6. ارائه داشبورد وب برای کاربران

---

## 🏗️ معماری فعلی پروژه

### ⚠️ مشکل اصلی: دوگانگی معماری

پروژه در حال حاضر از **دو فریمورک مختلف** به صورت همزمان استفاده می‌کند:

#### 1️⃣ FastAPI (فریمورک اصلی اولیه)
- **فایل اصلی:** `/srv/web/app.py` (1064 خط)
- **استفاده:** داشبورد وب، API endpoints
- **وضعیت:** نیمه‌کاره، برخی endpoint‌ها کامل نیستند

#### 2️⃣ Django (اضافه شده بعداً)
- **فایل اصلی:** `/srv/forex_assistant/settings.py`
- **استفاده:** مدیریت کاربران، احراز هویت، سیستم ایمیل
- **وضعیت:** کامل‌تر، با Celery و PostgreSQL

### 🔀 ساختار فعلی (مختلط و نامنظم)

```
/srv/
├── 📂 web/                    # FastAPI Application
│   ├── app.py                 # 1064 خط - FastAPI endpoints
│   ├── services/              # سرویس‌های FastAPI
│   ├── templates/             # Jinja2 templates
│   └── static/                # فایل‌های استاتیک
│
├── 📂 forex_assistant/        # Django Project
│   ├── settings.py            # تنظیمات Django
│   ├── urls.py                # URL routing
│   ├── celery.py              # Celery config
│   └── wsgi.py / asgi.py
│
├── 📂 apps/                   # Django Apps
│   ├── accounts/              # مدیریت کاربران (کامل)
│   ├── analysis/              # تحلیل بازار (کامل)
│   ├── trading/               # معاملات (ناقص - TODO زیاد)
│   └── scraping/              # اسکرپینگ (ناقص - TODO زیاد)
│
├── 📂 scrapers/               # ماژول‌های اسکرپینگ (مستقل)
│   ├── base_scraper.py
│   ├── investing_scraper.py
│   ├── forexfactory_scraper.py
│   ├── dailyfx_scraper.py
│   ├── fxstreet_scraper.py
│   └── forexlive_scraper.py
│
├── 📂 llm/                    # AI/LLM ماژول‌ها (مستقل)
│   ├── analyzer.py            # 39002 خط - تحلیلگر اصلی
│   ├── chart_analyzer.py      # تحلیل چارت با Vision API
│   └── prompts.py             # پرامپت‌های GPT
│
├── 📂 trading/                # ماژول‌های معاملاتی (مستقل)
│   ├── base_robot.py
│   ├── unified_robots.py
│   ├── robot_manager.py
│   ├── support_resistance.py  # 34910 خط!
│   └── ... (13 فایل)
│
├── 📂 strategy_bots/          # ربات‌های استراتژیک (مستقل)
│   ├── base_bot.py
│   ├── rsi_bot.py
│   └── ... (18 فایل)
│
├── 📂 indicators/             # اندیکاتورها و ابزارها (مستقل)
│   ├── risk_manager.py
│   └── trade_executor.py      # اتصال به MT5
│
├── 📂 config/                 # تنظیمات FastAPI (قدیمی)
│   └── settings.py
│
├── 📂 templates/              # Django templates
│   └── emails/                # 9 template ایمیل
│
├── main.py                    # FastAPI entry point
├── scheduler.py               # Scheduler مستقل
├── trading_bot.py             # Trading bot مستقل
└── manage.py                  # Django entry point
```

---

## 🔴 مشکلات شناسایی شده

### 1. دوگانگی فریمورک
- **FastAPI** و **Django** به صورت موازی اجرا می‌شوند
- هیچ یکپارچگی مشخصی بین آن‌ها وجود ندارد
- برخی قابلیت‌ها تکراری هستند

### 2. ماژول‌های مستقل پراکنده
- `scrapers/` - مستقل از Django
- `llm/` - مستقل از Django
- `trading/` - مستقل از Django
- `strategy_bots/` - مستقل از Django
- `indicators/` - مستقل از Django

این ماژول‌ها در اصل برای FastAPI نوشته شده‌اند ولی Django apps جدید سعی دارند از آن‌ها استفاده کنند.

### 3. TODO و کدهای ناقص

#### در `apps/scraping/`:
```python
# TODO: PRIORITY_NEXT - Integrate with existing scrapers/ module
# TODO: PRIORITY_NEXT - Use Celery task with scrapers/scraper_manager.py
```

#### در `apps/trading/`:
```python
# TODO: PRIORITY_NEXT - Integrate with existing trading/ module
# TODO: PRIORITY_NEXT - Integrate with web/services/trading_accounts.py
# TODO: PRIORITY_NEXT - Encrypt password using web/services/encryption.py
# TODO: PRIORITY_NEXT - Connect to broker and verify credentials
```

#### در `apps/analysis/`:
```python
# TODO: PRIORITY_NEXT - Implement full analysis for all pairs
# TODO: PRIORITY_NEXT - Implement MTF analysis with llm/analyzer.py
# TODO: PRIORITY_NEXT - Integrate with llm/analyzer.py for translation
```

### 4. فایل‌های تست پراکنده
```
/srv/test_email.py
/srv/test_email_container.py
/srv/test_email_django.py
/srv/test_smtp_simple.py
```

### 5. مستندات پراکنده و تکراری
```
/srv/README.md                      # مستندات اصلی (قدیمی)
/srv/CHART_ANALYSIS_UPGRADE.md      # مستندات ویژگی خاص
/srv/DAILY_SUMMARY_GUIDE.md         # راهنمای ویژگی
/srv/EMAIL_SYSTEM_README.md         # راهنمای سیستم ایمیل
/srv/EMAIL_DEPLOYMENT_SUMMARY.md    # خلاصه deploy
/srv/GMAIL_SETUP_GUIDE.md           # راهنمای Gmail
/srv/apps/analysis/README.md        # مستندات app
/srv/deploy/README.md               # راهنمای deploy
/srv/deploy/README_VPS.md           # راهنمای VPS
```

### 6. تنظیمات دوگانه
- `/srv/config/settings.py` - تنظیمات FastAPI
- `/srv/forex_assistant/settings.py` - تنظیمات Django
- برخی تنظیمات تکراری هستند

---

## ✅ بخش‌های کامل و کارآمد

### 1. سیستم احراز هویت (`apps/accounts/`)
- ✅ مدل User سفارشی
- ✅ Token-based authentication
- ✅ Email verification
- ✅ Password reset
- ✅ سیستم ایمیل کامل با 9 template

### 2. سیستم تحلیل (`apps/analysis/`)
- ✅ مدل‌های CurrencyPair, MarketAnalysis, DailySummary
- ✅ Chart analysis با TradingView
- ✅ Multi-timeframe analysis
- ✅ AI-powered analysis

### 3. Scrapers (ماژول مستقل)
- ✅ 5 scraper کامل و کارآمد
- ✅ ScraperManager برای مدیریت
- ✅ NewsArticle model

### 4. LLM Analyzer (ماژول مستقل)
- ✅ ForexAnalyzer با قابلیت‌های پیشرفته
- ✅ ChartImageAnalyzer برای تحلیل چارت
- ✅ پرامپت‌های حرفه‌ای

### 5. Celery Tasks
- ✅ پیکربندی کامل
- ✅ Periodic tasks برای email reminders
- ✅ Redis به عنوان broker

### 6. Docker Deployment
- ✅ docker-compose.yml کامل
- ✅ PostgreSQL + Redis
- ✅ Celery worker + beat
- ✅ Nginx (optional)

---

## 🔧 بخش‌های ناقص

### 1. Django Apps ناقص

#### `apps/scraping/`
- ❌ فقط اسکلت وجود دارد
- ❌ هیچ ادغامی با `scrapers/` انجام نشده
- ❌ Celery tasks خالی هستند

#### `apps/trading/`
- ❌ مدل‌ها وجود دارند ولی views ناقص
- ❌ هیچ ادغامی با `trading/` و `strategy_bots/` نیست
- ❌ اتصال به broker پیاده‌سازی نشده

### 2. FastAPI Endpoints ناقص
- ❌ برخی endpoint‌ها placeholder هستند
- ❌ Authentication ناقص
- ❌ ادغام با Django نشده

### 3. Frontend
- ⚠️ Templates موجود هستند ولی ناقص
- ⚠️ هیچ framework مدرن (React/Vue) نیست
- ⚠️ UI/UX ساده و قدیمی

---

## 📈 فایل‌های بزرگ و پیچیده

| فایل | خطوط | وضعیت |
|------|------|-------|
| `/srv/llm/analyzer.py` | 39,002 | ✅ کامل ولی نیاز به ریفکتور |
| `/srv/trading/support_resistance.py` | 34,910 | ✅ کامل ولی خیلی بزرگ |
| `/srv/trading/advanced_sl_strategies.py` | 39,100 | ✅ کامل |
| `/srv/trading/advanced_tp_strategies.py` | 30,809 | ✅ کامل |
| `/srv/web/app.py` | 1,064 | ⚠️ نیمه‌کاره |
| `/srv/apps/analysis/services.py` | 24,358 | ✅ کامل |

---

## 🎯 استراتژی پیشنهادی برای بازسازی

### گزینه 1: Django-First (پیشنهاد شده)
1. Django را به عنوان فریمورک اصلی نگه داریم
2. FastAPI را به عنوان API gateway اختیاری حفظ کنیم
3. ماژول‌های مستقل را به Django apps تبدیل کنیم
4. یکپارچه‌سازی کامل

### گزینه 2: FastAPI-First
1. FastAPI را به عنوان فریمورک اصلی نگه داریم
2. Django را فقط برای Admin و ORM استفاده کنیم
3. ادغام دو فریمورک

### گزینه 3: Microservices
1. جدا کردن کامل سرویس‌ها
2. API Gateway
3. پیچیدگی بالا

**انتخاب: گزینه 1 (Django-First)** چون:
- Django apps بیشتر توسعه یافته‌اند
- Celery، Email، Auth همه با Django هستند
- Docker setup برای Django است
- FastAPI فقط برای چند endpoint استفاده شده

---

## 📋 اولویت‌بندی کارها

### Priority HIGH (فوری)
1. ✅ تحلیل کامل پروژه (این فایل)
2. ⏳ ایجاد PENDING_TASKS.md
3. ⏳ ادغام `scrapers/` با `apps/scraping/`
4. ⏳ ادغام `trading/` با `apps/trading/`
5. ⏳ بازنویسی مستندات اصلی

### Priority MEDIUM
6. ⏳ ریفکتور فایل‌های بزرگ
7. ⏳ حذف کدهای تکراری
8. ⏳ بهینه‌سازی queries
9. ⏳ تست‌های واحد

### Priority LOW
10. ⏳ Frontend modernization
11. ⏳ API documentation
12. ⏳ Performance optimization

---

## 🔍 نتیجه‌گیری

این پروژه یک **سیستم پیچیده و قدرتمند** است که توسط چند مرحله AI ساخته شده و دارای:

✅ **نقاط قوت:**
- ماژول‌های AI قدرتمند
- Scrapers کامل و کارآمد
- سیستم معاملاتی پیشرفته
- Docker deployment آماده

❌ **نقاط ضعف:**
- دوگانگی معماری (Django + FastAPI)
- کدهای ناقص و TODO زیاد
- مستندات پراکنده
- ادغام ناقص بین ماژول‌ها

**وضعیت کلی:** 60% کامل، 40% ناقص یا نیاز به بازسازی

---

**مرحله بعدی:** ایجاد PENDING_TASKS.md با لیست دقیق تمام کارهای باقی‌مانده
