# 📋 لیست کارهای ناقص و باقی‌مانده

**تاریخ:** 2025-12-22  
**وضعیت پروژه:** 60% کامل، 40% ناقص

---

## 🔴 HIGH PRIORITY - کارهای فوری و حیاتی

### 1. ادغام Scrapers با Django App
**محل:** `/srv/apps/scraping/` + `/srv/scrapers/`

**مشکل:**
- ماژول `scrapers/` به صورت مستقل کار می‌کند
- Django app `apps/scraping/` فقط اسکلت است و هیچ ادغامی انجام نشده
- Celery tasks خالی هستند

**فایل‌های مربوطه:**
```
/srv/apps/scraping/views.py      # TODO: PRIORITY_NEXT
/srv/apps/scraping/tasks.py      # TODO: PRIORITY_NEXT
/srv/scrapers/scraper_manager.py # کامل و کارآمد
```

**راه‌حل پیشنهادی:**
1. ایجاد service layer در `apps/scraping/services.py`
2. Wrapper برای `ScraperManager` از `scrapers/`
3. پیاده‌سازی Celery tasks واقعی
4. ایجاد API endpoints کامل

**کد نمونه:**
```python
# apps/scraping/services.py
from scrapers import ScraperManager
from django.conf import settings

class ScrapingService:
    def __init__(self):
        self.scraper_manager = ScraperManager(settings.DATA_DIR)
    
    async def scrape_all_sources(self, pairs=None):
        """Scrape news from all sources"""
        return await self.scraper_manager.scrape_all(pairs)
```

**اولویت:** ⭐⭐⭐⭐⭐ (بسیار بالا)

---

### 2. ادغام Trading Modules با Django App
**محل:** `/srv/apps/trading/` + `/srv/trading/` + `/srv/strategy_bots/`

**مشکل:**
- 3 ماژول جداگانه برای trading وجود دارد:
  - `apps/trading/` - Django app (ناقص)
  - `trading/` - ماژول‌های پیشرفته (13 فایل، کامل)
  - `strategy_bots/` - ربات‌های استراتژیک (18 فایل، کامل)
- هیچ ادغامی بین آن‌ها نیست
- Views در `apps/trading/` همه TODO دارند

**فایل‌های مربوطه:**
```
/srv/apps/trading/views.py                    # TODO زیاد
/srv/trading/robot_manager.py                 # کامل - 15518 خط
/srv/trading/unified_robots.py                # کامل - 15808 خط
/srv/strategy_bots/base_bot.py                # کامل - 11774 خط
/srv/strategy_bots/rsi_bot.py                 # کامل - 21550 خط
```

**TODO های شناسایی شده:**
```python
# apps/trading/views.py
# TODO: PRIORITY_NEXT - Integrate with web/services/trading_accounts.py
# TODO: PRIORITY_NEXT - Integrate with web/services/broker_connectors.py
# TODO: PRIORITY_NEXT - Encrypt password using web/services/encryption.py
# TODO: PRIORITY_NEXT - Connect to broker and verify credentials
# TODO: PRIORITY_NEXT - Integrate with trading/unified_robots.py
# TODO: PRIORITY_NEXT - Integrate with trading/robot_manager.py
```

**راه‌حل پیشنهادی:**
1. ایجاد `apps/trading/services/` با:
   - `robot_service.py` - wrapper برای `trading/robot_manager.py`
   - `strategy_service.py` - wrapper برای `strategy_bots/`
   - `broker_service.py` - مدیریت اتصال به broker
2. پیاده‌سازی کامل views
3. ایجاد serializers برای robot configs
4. Celery tasks برای اجرای خودکار ربات‌ها

**اولویت:** ⭐⭐⭐⭐⭐ (بسیار بالا)

---

### 3. تکمیل Analysis Views
**محل:** `/srv/apps/analysis/views.py`

**مشکل:**
- برخی endpoint‌ها placeholder هستند
- Multi-timeframe analysis ناقص است
- Translation endpoint پیاده‌سازی نشده

**TODO های شناسایی شده:**
```python
# Line 181-182
# TODO: PRIORITY_NEXT - Implement full analysis for all pairs

# Line 287-293
# TODO: PRIORITY_NEXT - Implement MTF analysis with llm/analyzer.py

# Line 306-309
# TODO: PRIORITY_NEXT - Integrate with llm/analyzer.py for translation
```

**راه‌حل پیشنهادی:**
1. استفاده از `llm.analyzer.ForexAnalyzer` موجود
2. پیاده‌سازی multi-timeframe با `chart_analyzer.py`
3. اضافه کردن translation با OpenAI API

**اولویت:** ⭐⭐⭐⭐ (بالا)

---

### 4. یکپارچه‌سازی FastAPI و Django
**محل:** `/srv/web/app.py` + `/srv/forex_assistant/`

**مشکل:**
- دو فریمورک به صورت موازی کار می‌کنند
- FastAPI endpoints برخی قابلیت‌های Django را تکرار می‌کنند
- Authentication بین دو فریمورک یکپارچه نیست

**فایل‌های مربوطه:**
```
/srv/web/app.py              # 1064 خط FastAPI
/srv/main.py                 # FastAPI entry point
/srv/manage.py               # Django entry point
```

**راه‌حل‌های ممکن:**

**گزینه A (پیشنهادی):** Django-First
- حذف FastAPI endpoints تکراری
- استفاده از Django REST Framework برای همه API ها
- نگه داشتن FastAPI فقط برای real-time features (اگر نیاز باشد)

**گزینه B:** FastAPI-First
- استفاده از Django فقط برای ORM و Admin
- انتقال همه endpoints به FastAPI
- پیچیدگی بیشتر

**گزینه C:** Hybrid
- Django برای CRUD و Admin
- FastAPI برای real-time و WebSocket
- نیاز به API Gateway

**اولویت:** ⭐⭐⭐⭐ (بالا)

---

## 🟡 MEDIUM PRIORITY - کارهای مهم ولی غیرفوری

### 5. ریفکتور فایل‌های بزرگ

#### 5.1. `/srv/llm/analyzer.py` (39,002 خط!)
**مشکل:**
- یک فایل غول‌پیکر با 39 هزار خط کد
- چندین کلاس و متد در یک فایل
- سخت برای نگهداری و debug

**راه‌حل:**
```
/srv/llm/
├── __init__.py
├── base_analyzer.py          # کلاس پایه
├── forex_analyzer.py         # تحلیل فارکس
├── sentiment_analyzer.py     # تحلیل احساسات
├── news_analyzer.py          # تحلیل اخبار
├── recommendation_engine.py  # موتور پیشنهاد
└── utils.py                  # توابع کمکی
```

**اولویت:** ⭐⭐⭐

---

#### 5.2. `/srv/trading/support_resistance.py` (34,910 خط!)
**مشکل:**
- فایل بسیار بزرگ برای محاسبات Support/Resistance
- احتمالاً شامل الگوریتم‌های مختلف

**راه‌حل:**
```
/srv/trading/support_resistance/
├── __init__.py
├── base.py                   # کلاس پایه
├── pivot_points.py           # Pivot Points
├── fibonacci.py              # Fibonacci Levels
├── swing_points.py           # Swing Highs/Lows
└── volume_profile.py         # Volume-based S/R
```

**اولویت:** ⭐⭐⭐

---

#### 5.3. `/srv/trading/advanced_sl_strategies.py` (39,100 خط)
**مشکل:**
- فایل بسیار بزرگ برای استراتژی‌های Stop Loss

**راه‌حل:**
- تقسیم به فایل‌های کوچک‌تر بر اساس نوع استراتژی
- ایجاد factory pattern برای انتخاب استراتژی

**اولویت:** ⭐⭐⭐

---

### 6. بهینه‌سازی Database Queries

**مشکل‌های احتمالی:**
- N+1 queries در list views
- عدم استفاده از `select_related` و `prefetch_related`
- Queries تکراری

**فایل‌های نیازمند بررسی:**
```
/srv/apps/analysis/views.py
/srv/apps/trading/views.py
/srv/apps/accounts/views.py
```

**راه‌حل:**
1. استفاده از Django Debug Toolbar
2. اضافه کردن `select_related` و `prefetch_related`
3. ایجاد custom QuerySets
4. استفاده از caching (Redis)

**اولویت:** ⭐⭐⭐

---

### 7. حذف کدهای تکراری

**موارد شناسایی شده:**

#### 7.1. تنظیمات دوگانه
```
/srv/config/settings.py          # FastAPI settings
/srv/forex_assistant/settings.py # Django settings
```
**راه‌حل:** ادغام در یک فایل

#### 7.2. Pair Configuration
```python
# در چند جا تکرار شده:
- /srv/config/settings.py (PAIR_CONFIGS)
- /srv/forex_assistant/settings.py (PAIR_CONFIGS)
- /srv/data/pairs.json
```
**راه‌حل:** استفاده فقط از database (CurrencyPair model)

**اولویت:** ⭐⭐⭐

---

### 8. مستندسازی API

**مشکل:**
- هیچ مستندات API جامعی وجود ندارد
- Swagger/OpenAPI تنظیم نشده
- نمونه‌های request/response ناقص

**راه‌حل:**
1. استفاده از `drf-spectacular` برای Django REST
2. یا `FastAPI` automatic docs
3. ایجاد فایل `API.md` با:
   - تمام endpoints
   - Authentication
   - Request/Response examples
   - Error codes

**اولویت:** ⭐⭐⭐

---

### 9. تست‌های واحد (Unit Tests)

**مشکل:**
- هیچ تستی وجود ندارد!
- کد بدون تست خطرناک است

**راه‌حل:**
```
/srv/apps/accounts/tests/
├── test_models.py
├── test_views.py
├── test_serializers.py
└── test_services.py

/srv/apps/analysis/tests/
├── test_models.py
├── test_views.py
└── test_services.py
```

**حداقل تست‌های مورد نیاز:**
- User authentication
- Token generation/validation
- Email sending
- Scraping functionality
- Analysis generation

**اولویت:** ⭐⭐⭐

---

## 🟢 LOW PRIORITY - کارهای اختیاری و بهبودها

### 10. Frontend Modernization

**مشکل:**
- Templates ساده و قدیمی
- هیچ framework مدرن (React/Vue) نیست
- UI/UX ساده

**راه‌حل:**
1. ایجاد frontend جداگانه با React/Vue
2. یا استفاده از Alpine.js برای interactivity
3. بهبود UI با Tailwind CSS

**اولویت:** ⭐⭐

---

### 11. WebSocket برای Real-time Updates

**مشکل:**
- هیچ قابلیت real-time نیست
- کاربر باید صفحه را refresh کند

**راه‌حل:**
- استفاده از Django Channels
- یا FastAPI WebSocket
- ارسال real-time:
  - قیمت‌های لحظه‌ای
  - سیگنال‌های جدید
  - وضعیت ربات‌ها

**اولویت:** ⭐⭐

---

### 12. Monitoring و Logging پیشرفته

**مشکل:**
- Logging ساده است
- هیچ monitoring tool نیست

**راه‌حل:**
1. استفاده از Sentry برای error tracking
2. Prometheus + Grafana برای metrics
3. ELK Stack برای log aggregation

**اولویت:** ⭐⭐

---

### 13. CI/CD Pipeline

**مشکل:**
- هیچ CI/CD نیست
- Deploy دستی است

**راه‌حل:**
- GitHub Actions یا GitLab CI
- Automated testing
- Automated deployment

**اولویت:** ⭐⭐

---

### 14. Security Hardening

**موارد نیازمند بررسی:**
- [ ] SQL Injection protection (Django ORM خوب است)
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] Rate limiting
- [ ] Input validation
- [ ] Password hashing (Django خوب است)
- [ ] API key encryption
- [ ] HTTPS enforcement

**اولویت:** ⭐⭐

---

## 📝 فایل‌های نیازمند پاکسازی

### فایل‌های تست موقت
```
/srv/test_email.py
/srv/test_email_container.py
/srv/test_email_django.py
/srv/test_smtp_simple.py
```
**اقدام:** انتقال به `/srv/tests/` یا حذف

### مستندات پراکنده
```
/srv/CHART_ANALYSIS_UPGRADE.md
/srv/DAILY_SUMMARY_GUIDE.md
/srv/EMAIL_SYSTEM_README.md
/srv/EMAIL_DEPLOYMENT_SUMMARY.md
/srv/GMAIL_SETUP_GUIDE.md
```
**اقدام:** ادغام در مستندات اصلی

---

## 🎯 خلاصه اولویت‌بندی

### این هفته (HIGH):
1. ✅ تحلیل کامل پروژه
2. ⏳ ادغام Scrapers با Django
3. ⏳ ادغام Trading modules با Django
4. ⏳ تکمیل Analysis views
5. ⏳ تصمیم‌گیری درباره FastAPI vs Django

### هفته آینده (MEDIUM):
6. ⏳ ریفکتور فایل‌های بزرگ
7. ⏳ بهینه‌سازی queries
8. ⏳ حذف کدهای تکراری
9. ⏳ مستندسازی API
10. ⏳ نوشتن تست‌های واحد

### ماه آینده (LOW):
11. ⏳ Frontend modernization
12. ⏳ WebSocket implementation
13. ⏳ Monitoring setup
14. ⏳ CI/CD pipeline
15. ⏳ Security audit

---

## 📊 آمار کلی

| وضعیت | تعداد | درصد |
|-------|-------|------|
| ✅ کامل | 6 بخش | 40% |
| ⚠️ نیمه‌کاره | 5 بخش | 33% |
| ❌ ناقص | 4 بخش | 27% |

**زمان تخمینی برای تکمیل:**
- HIGH Priority: 2-3 هفته
- MEDIUM Priority: 3-4 هفته
- LOW Priority: 1-2 ماه

---

**یادداشت:** این لیست زنده است و با پیشرفت پروژه به‌روز می‌شود.
