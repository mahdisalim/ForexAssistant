# 🚀 راهنمای نصب و راه‌اندازی

**نسخه:** 2.0  
**تاریخ:** 2025-12-22

---

## 📋 فهرست مطالب

1. [پیش‌نیازها](#پیش‌نیازها)
2. [نصب با Docker (پیشنهادی)](#نصب-با-docker)
3. [نصب دستی](#نصب-دستی)
4. [پیکربندی](#پیکربندی)
5. [اجرای برنامه](#اجرای-برنامه)
6. [تست](#تست)
7. [عیب‌یابی](#عیب‌یابی)

---

## 📦 پیش‌نیازها

### نیازمندی‌های سیستم

#### برای نصب با Docker:
- **Docker:** نسخه 20.10 یا بالاتر
- **Docker Compose:** نسخه 2.0 یا بالاتر
- **RAM:** حداقل 4GB (پیشنهادی 8GB)
- **Storage:** حداقل 10GB فضای خالی

#### برای نصب دستی:
- **Python:** 3.10 یا بالاتر
- **PostgreSQL:** 15 یا بالاتر
- **Redis:** 7 یا بالاتر
- **Node.js:** 18+ (اختیاری - برای frontend)
- **Playwright:** برای chart screenshots

### API Keys مورد نیاز

1. **OpenAI API Key** (ضروری)
   - ثبت‌نام: https://platform.openai.com/signup
   - دریافت API Key: https://platform.openai.com/api-keys
   - هزینه: Pay-as-you-go

2. **Gmail App Password** (برای ارسال ایمیل)
   - فعال‌سازی 2-Step Verification
   - دریافت App Password: https://myaccount.google.com/apppasswords

3. **MetaTrader 5 Account** (اختیاری - برای trading)
   - حساب Demo یا Live
   - اطلاعات: Login, Password, Server

---

## 🐳 نصب با Docker (پیشنهادی)

### مرحله 1: دانلود پروژه

```bash
# Clone repository
git clone https://github.com/yourusername/forex-analysis-assistant.git
cd forex-analysis-assistant
```

### مرحله 2: پیکربندی Environment Variables

```bash
# کپی فایل نمونه
cp .env.example .env

# ویرایش فایل .env
nano .env
```

**حداقل تنظیمات مورد نیاز:**
```env
# Django
SECRET_KEY=your-very-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
POSTGRES_DB=forex_assistant
POSTGRES_USER=forex_user
POSTGRES_PASSWORD=your-secure-password

# OpenAI (ضروری)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Email (برای نوتیفیکیشن‌ها)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### مرحله 3: Build و اجرا

```bash
cd deploy

# Build images
docker compose build

# اجرای containers
docker compose up -d

# مشاهده logs
docker compose logs -f
```

### مرحله 4: اجرای Migrations

```bash
# اجرای migrations
docker compose exec web python manage.py migrate

# ایجاد superuser
docker compose exec web python manage.py createsuperuser
```

### مرحله 5: جمع‌آوری Static Files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### ✅ تست نصب

```bash
# بررسی وضعیت containers
docker compose ps

# تست API
curl http://localhost:8000/api/health/

# دسترسی به Admin Panel
# http://localhost:8000/admin/
```

---

## 💻 نصب دستی

### مرحله 1: نصب Dependencies سیستم

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y build-essential libpq-dev
```

#### macOS:
```bash
brew install python@3.10
brew install postgresql@15
brew install redis
```

#### Windows:
```powershell
# نصب Python از python.org
# نصب PostgreSQL از postgresql.org
# نصب Redis از https://github.com/microsoftarchive/redis/releases
```

### مرحله 2: ایجاد Virtual Environment

```bash
# ایجاد venv
python3.10 -m venv venv

# فعال‌سازی
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### مرحله 3: نصب Python Packages

```bash
# نصب dependencies
pip install --upgrade pip
pip install -r requirements.txt

# نصب Playwright browsers
playwright install chromium
```

### مرحله 4: راه‌اندازی PostgreSQL

```bash
# ورود به PostgreSQL
sudo -u postgres psql

# ایجاد database و user
CREATE DATABASE forex_assistant;
CREATE USER forex_user WITH PASSWORD 'your_password';
ALTER ROLE forex_user SET client_encoding TO 'utf8';
ALTER ROLE forex_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE forex_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE forex_assistant TO forex_user;
\q
```

### مرحله 5: راه‌اندازی Redis

```bash
# شروع Redis
# Linux:
sudo systemctl start redis
sudo systemctl enable redis

# macOS:
brew services start redis

# Windows:
redis-server
```

### مرحله 6: پیکربندی Environment

```bash
# کپی .env.example
cp .env.example .env

# ویرایش .env
nano .env
```

**تنظیمات برای نصب دستی:**
```env
# Database
DATABASE_URL=postgres://forex_user:your_password@localhost:5432/forex_assistant

# Redis
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# سایر تنظیمات مشابه نصب Docker
```

### مرحله 7: اجرای Migrations

```bash
# اجرای migrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# جمع‌آوری static files
python manage.py collectstatic --noinput
```

---

## ⚙️ پیکربندی

### 1. تنظیمات OpenAI

```env
# .env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1  # یا proxy خودتان
OPENAI_MODEL=gpt-4o-mini  # یا gpt-4o برای کیفیت بالاتر
```

**تست اتصال:**
```bash
docker compose exec web python -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('✓ OpenAI connected:', response.choices[0].message.content)
"
```

### 2. تنظیمات Gmail

**مراحل دریافت App Password:**

1. فعال‌سازی 2-Step Verification:
   - https://myaccount.google.com/security
   - 2-Step Verification → Turn On

2. ایجاد App Password:
   - https://myaccount.google.com/apppasswords
   - Select app: Mail
   - Select device: Other (Custom name)
   - کپی password 16 رقمی (بدون فاصله)

3. تنظیم در .env:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # 16 رقمی بدون فاصله
DEFAULT_FROM_EMAIL=your-email@gmail.com
EMAIL_FROM_NAME=Forex Assistant
```

**تست ارسال ایمیل:**
```bash
docker compose exec web python -c "
from apps.accounts.email_service import get_email_service
from apps.accounts.models import User

email_service = get_email_service()
user = User.objects.first()
if user:
    verification = email_service.send_verification_email(user, 'fa')
    print(f'✓ Email sent! Code: {verification.code}')
"
```

### 3. تنظیمات Currency Pairs

**روش 1: از طریق Admin Panel**
```
1. http://localhost:8000/admin/
2. Analysis → Currency Pairs
3. Add Currency Pair
4. تنظیم: symbol, tradingview_symbol, volatility, SL/TP pips
```

**روش 2: از طریق فایل JSON**
```bash
# ویرایش /srv/data/pairs.json
nano /srv/data/pairs.json
```

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

### 4. تنظیمات Celery

**Celery Beat Schedule** (در `forex_assistant/celery.py`):
```python
app.conf.beat_schedule = {
    'check-subscription-expiry-daily': {
        'task': 'apps.accounts.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),  # هر روز 9 صبح
    },
}
```

**تست Celery:**
```bash
# بررسی worker
docker compose exec celery_worker celery -A forex_assistant inspect active

# بررسی scheduled tasks
docker compose exec celery_beat celery -A forex_assistant inspect scheduled
```

---

## 🏃 اجرای برنامه

### با Docker:

```bash
cd /srv/deploy

# شروع همه سرویس‌ها
docker compose up -d

# مشاهده logs
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f celery_beat

# توقف
docker compose down

# Restart
docker compose restart web
```

### نصب دستی:

**Terminal 1 - Django Server:**
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A forex_assistant worker -l info
```

**Terminal 3 - Celery Beat:**
```bash
source venv/bin/activate
celery -A forex_assistant beat -l info
```

**Terminal 4 - FastAPI (اختیاری):**
```bash
source venv/bin/activate
python main.py
```

---

## 🧪 تست

### 1. Health Check

```bash
# API health
curl http://localhost:8000/api/health/

# Expected response:
# {"status":"healthy","timestamp":"2025-12-22T..."}
```

### 2. تست Authentication

```bash
# ثبت‌نام
curl -X POST http://localhost:8000/api/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'

# ورود
curl -X POST http://localhost:8000/api/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### 3. تست Analysis API

```bash
# لیست pairs
curl http://localhost:8000/api/pairs/

# تحلیل یک pair
curl http://localhost:8000/api/analysis/EURUSD/

# خلاصه روزانه
curl "http://localhost:8000/api/summary/?asset=USD&lang=fa"
```

### 4. تست Scraping

```bash
# اجرای دستی scraper
docker compose exec web python -c "
import asyncio
from scrapers import ScraperManager
from pathlib import Path

async def test():
    manager = ScraperManager(Path('/app/data'))
    articles = await manager.scrape_all(['EURUSD', 'XAUUSD'])
    print(f'✓ Scraped {len(articles)} articles')
    for article in articles[:3]:
        print(f'  - {article.title}')

asyncio.run(test())
"
```

### 5. تست Email System

```bash
# تست SMTP connection
docker compose exec web python test_smtp_simple.py

# تست Django email service
docker compose exec web python test_email_container.py
```

---

## 🐛 عیب‌یابی

### مشکل: Container ها start نمی‌شوند

```bash
# بررسی logs
docker compose logs

# بررسی وضعیت
docker compose ps

# Rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### مشکل: Database connection error

```bash
# بررسی PostgreSQL
docker compose exec db psql -U forex_user -d forex_assistant

# اگر خطا داد، restart کنید
docker compose restart db
docker compose restart web
```

### مشکل: OpenAI API error

```bash
# بررسی API key
docker compose exec web env | grep OPENAI_API_KEY

# تست مستقیم
docker compose exec web python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
print('API Key:', openai.api_key[:20] + '...')
"
```

### مشکل: Email ارسال نمی‌شود

```bash
# بررسی تنظیمات
docker compose exec web env | grep EMAIL

# تست SMTP
docker compose exec web python test_smtp_simple.py

# بررسی Celery logs
docker compose logs celery_worker
```

### مشکل: Celery tasks اجرا نمی‌شوند

```bash
# بررسی Redis
docker compose exec redis redis-cli ping
# باید "PONG" برگرداند

# بررسی Celery worker
docker compose exec celery_worker celery -A forex_assistant inspect active

# Restart Celery
docker compose restart celery_worker celery_beat
```

### مشکل: Chart screenshots کار نمی‌کنند

```bash
# نصب Playwright browsers
docker compose exec web playwright install chromium

# یا در نصب دستی:
playwright install chromium

# تست
docker compose exec web python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('✓ Playwright working')
    browser.close()
"
```

### مشکل: Port already in use

```bash
# پیدا کردن process
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# یا تغییر port در docker-compose.yml
ports:
  - "8001:8000"  # استفاده از port 8001
```

---

## 📊 بررسی وضعیت سیستم

### Dashboard URLs

```
Admin Panel:     http://localhost:8000/admin/
Landing Page:    http://localhost:8000/
Dashboard:       http://localhost:8000/dashboard/
API Docs:        http://localhost:8000/api/docs/  (FastAPI)
```

### Monitoring Commands

```bash
# وضعیت containers
docker compose ps

# مصرف منابع
docker stats

# Disk usage
docker system df

# Logs
docker compose logs -f --tail=100 web
```

### Database Queries

```bash
# تعداد کاربران
docker compose exec web python manage.py shell -c "
from apps.accounts.models import User
print(f'Users: {User.objects.count()}')
"

# تعداد تحلیل‌ها
docker compose exec web python manage.py shell -c "
from apps.analysis.models import MarketAnalysis
print(f'Analyses: {MarketAnalysis.objects.count()}')
"
```

---

## 🔄 به‌روزرسانی

### Docker:

```bash
cd /srv/deploy

# Pull latest changes
git pull origin main

# Rebuild
docker compose down
docker compose build
docker compose up -d

# اجرای migrations جدید
docker compose exec web python manage.py migrate
```

### نصب دستی:

```bash
# Pull changes
git pull origin main

# فعال‌سازی venv
source venv/bin/activate

# به‌روزرسانی packages
pip install -r requirements.txt --upgrade

# اجرای migrations
python manage.py migrate

# Restart services
# (Ctrl+C در هر terminal و اجرای مجدد)
```

---

## 📝 نکات مهم

### Security Checklist:
- [ ] تغییر `SECRET_KEY` در production
- [ ] تنظیم `DEBUG=False` در production
- [ ] استفاده از HTTPS
- [ ] محدود کردن `ALLOWED_HOSTS`
- [ ] استفاده از strong passwords
- [ ] فعال‌سازی firewall
- [ ] Backup منظم database

### Performance Tips:
- [ ] استفاده از Redis برای caching
- [ ] تنظیم PostgreSQL connection pooling
- [ ] استفاده از CDN برای static files
- [ ] فعال‌سازی Gzip compression
- [ ] Monitoring با Prometheus/Grafana

### Backup:

```bash
# Backup database
docker compose exec db pg_dump -U forex_user forex_assistant > backup.sql

# Restore
docker compose exec -T db psql -U forex_user forex_assistant < backup.sql

# Backup data directory
tar -czf data_backup.tar.gz /srv/data/
```

---

## 🆘 دریافت کمک

- **مستندات:** `/srv/docs/`
- **Issues:** GitHub Issues
- **Email:** support@example.com
- **Logs:** `/srv/logs/`

---

**موفق باشید! 🚀**
