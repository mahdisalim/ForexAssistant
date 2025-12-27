# Forex Analysis Assistant - Docker Deployment

## راه‌اندازی سریع

### پیش‌نیازها
- Docker و Docker Compose نصب شده باشد
- در محیط WSL، Docker Desktop روی ویندوز باید در حال اجرا باشد

### مراحل راه‌اندازی

1. **کپی فایل تنظیمات:**
   ```bash
   cd /srv/deploy
   cp .env.example .env
   ```

2. **ویرایش تنظیمات:**
   ```bash
   nano .env
   ```
   حداقل `OPENAI_API_KEY` را تنظیم کنید.

3. **اجرای پروژه:**
   ```bash
   ./start.sh dev
   ```

4. **دسترسی از مرورگر ویندوز:**
   - آدرس: `http://localhost:8000`
   - یا: `http://127.0.0.1:8000`

### دستورات مفید

```bash
# شروع در حالت توسعه
./start.sh dev

# شروع در حالت production (با nginx)
./start.sh prod

# توقف
./start.sh stop

# مشاهده لاگ‌ها
./start.sh logs

# وضعیت کانتینرها
./start.sh status

# اجرای migrations
./start.sh migrate
```

## ساختار کانتینرها

| کانتینر | توضیحات | پورت |
|---------|---------|------|
| `forex_web` | Django Web Application | 8000 |
| `forex_db` | PostgreSQL Database | 5432 (internal) |
| `forex_redis` | Redis Cache & Broker | 6379 (internal) |
| `forex_celery_worker` | Celery Background Worker | - |
| `forex_celery_beat` | Celery Scheduler | - |
| `forex_nginx` | Nginx (production only) | 80 |

## دسترسی از ویندوز (WSL)

در محیط WSL، پورت‌ها به صورت خودکار به ویندوز forward می‌شوند:

1. مرورگر ویندوز را باز کنید
2. به آدرس `http://localhost:8000` بروید
3. یا از `http://127.0.0.1:8000` استفاده کنید

### اگر کار نکرد:
```bash
# IP آدرس WSL را پیدا کنید
hostname -I
```
سپس از آن IP در مرورگر ویندوز استفاده کنید.

## پنل مدیریت

- آدرس: `http://localhost:8000/admin/`
- کاربر پیش‌فرض: `admin@forex.local`
- رمز عبور: `admin123`

## TODO - کارهای باقی‌مانده

برای پیدا کردن بخش‌هایی که نیاز به تکمیل دارند، جستجو کنید:
```bash
grep -r "TODO: PRIORITY_NEXT" /srv/apps/
```

### اولویت‌های اصلی:
1. **تحلیل AI**: یکپارچه‌سازی با `llm/analyzer.py`
2. **اسکرپینگ**: یکپارچه‌سازی با `scrapers/`
3. **ربات‌های معاملاتی**: یکپارچه‌سازی با `trading/`
4. **اتصال به بروکر**: یکپارچه‌سازی با `web/services/broker_connectors.py`
