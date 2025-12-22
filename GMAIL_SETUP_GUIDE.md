# راهنمای راه‌اندازی Gmail برای ارسال ایمیل

## روش 1: استفاده از Gmail SMTP (ساده‌تر - توصیه می‌شود)

### مرحله 1: فعال‌سازی 2-Step Verification

1. به [Google Account](https://myaccount.google.com/) بروید
2. از منوی سمت چپ، **Security** را انتخاب کنید
3. در بخش "Signing in to Google"، روی **2-Step Verification** کلیک کنید
4. دستورالعمل‌ها را دنبال کرده و آن را فعال کنید

### مرحله 2: ایجاد App Password

1. بعد از فعال کردن 2-Step Verification، به [App Passwords](https://myaccount.google.com/apppasswords) بروید
2. در قسمت "Select app"، **Mail** را انتخاب کنید
3. در قسمت "Select device"، **Other (Custom name)** را انتخاب کنید
4. نام دلخواه وارد کنید (مثلاً: "Forex Assistant")
5. روی **Generate** کلیک کنید
6. **رمز 16 رقمی** نمایش داده می‌شود - آن را کپی کنید (فقط یک بار نمایش داده می‌شود!)

### مرحله 3: پیکربندی Django Settings

فایل `.env` خود را ویرایش کنید یا در `settings.py` اضافه کنید:

```python
# Email Configuration (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # ایمیل Gmail شما
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # App Password (16 رقمی)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
EMAIL_FROM_NAME = 'Forex Assistant'

# Frontend URL for email links
FRONTEND_URL = 'http://localhost:3000'  # یا دامنه اصلی شما
```

### مرحله 4: تست ارسال ایمیل

```python
from apps.accounts.email_service import get_email_service

# تست ارسال ایمیل
email_service = get_email_service()
success = email_service._send_email(
    to_email='test@example.com',
    subject='Test Email',
    html_content='<h1>Test</h1><p>This is a test email.</p>'
)
print(f"Email sent: {success}")
```

---

## روش 2: استفاده از Gmail API (پیشرفته‌تر)

### مرحله 1: ایجاد پروژه در Google Cloud Console

1. به [Google Cloud Console](https://console.cloud.google.com/) بروید
2. پروژه جدید بسازید یا یکی از پروژه‌های موجود را انتخاب کنید
3. نام پروژه را وارد کنید (مثلاً: "Forex Assistant Email")

### مرحله 2: فعال‌سازی Gmail API

1. در منوی سمت چپ، به **APIs & Services > Library** بروید
2. "Gmail API" را جستجو کنید
3. روی آن کلیک کرده و **Enable** را بزنید

### مرحله 3: ایجاد OAuth 2.0 Credentials

1. به **APIs & Services > Credentials** بروید
2. روی **Create Credentials** کلیک کنید
3. **OAuth client ID** را انتخاب کنید
4. اگر اولین بار است، باید **OAuth consent screen** را پیکربندی کنید:
   - User Type: **External** (برای تست) یا **Internal** (اگر G Suite دارید)
   - App name: "Forex Assistant"
   - User support email: ایمیل خودتان
   - Developer contact: ایمیل خودتان
   - Scopes: `https://www.googleapis.com/auth/gmail.send`
5. بعد از پیکربندی consent screen، دوباره Credentials بسازید:
   - Application type: **Web application**
   - Name: "Forex Assistant Web"
   - Authorized redirect URIs: `http://localhost:8000/oauth2callback` (برای تست)
6. فایل JSON credentials را دانلود کنید

### مرحله 4: نصب کتابخانه‌های لازم

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### مرحله 5: پیکربندی Django

فایل credentials.json را در مسیر `/srv/config/gmail_credentials.json` قرار دهید.

```python
# در settings.py
GMAIL_API_CREDENTIALS = BASE_DIR / 'config' / 'gmail_credentials.json'
GMAIL_API_TOKEN = BASE_DIR / 'config' / 'gmail_token.json'
```

---

## نصب Dependencies

فایل `requirements.txt` را آپدیت کنید:

```bash
# اضافه کردن به requirements.txt
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.110.0
```

نصب:
```bash
pip install -r requirements.txt
```

---

## راه‌اندازی Celery برای یادآوری‌های خودکار

### مرحله 1: نصب Redis (اگر نصب نیست)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# شروع Redis
redis-server
```

### مرحله 2: پیکربندی Celery

در `config/celery.py` (اگر وجود ندارد، بسازید):

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')

app = Celery('forex_assistant')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'check-subscription-expiry-daily': {
        'task': 'apps.accounts.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),  # هر روز ساعت 9 صبح
    },
    'check-expired-subscriptions-daily': {
        'task': 'apps.accounts.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=10, minute=0),  # هر روز ساعت 10 صبح
    },
}
```

### مرحله 3: اجرای Celery Worker و Beat

```bash
# Terminal 1: Celery Worker
celery -A config worker -l info

# Terminal 2: Celery Beat (برای task‌های زمان‌بندی شده)
celery -A config beat -l info
```

---

## Migration و Admin

### اجرای Migration

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### ثبت مدل‌ها در Admin

فایل `apps/accounts/admin.py` را آپدیت کنید:

```python
from django.contrib import admin
from .models import (
    User, AuthToken, EmailVerification, 
    PasswordResetToken, EmailNotification
)

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'code']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']

@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'subject', 'sent_at', 'is_successful']
    list_filter = ['notification_type', 'is_successful', 'sent_at']
    search_fields = ['user__email', 'subject']
    date_hierarchy = 'sent_at'
```

---

## نمونه استفاده

### 1. ارسال کد تایید ایمیل

```python
from apps.accounts.email_service import get_email_service
from apps.accounts.models import User

user = User.objects.get(email='user@example.com')
email_service = get_email_service()

# ارسال کد تایید
verification = email_service.send_verification_email(user, language='fa')
if verification:
    print(f"Verification code: {verification.code}")
```

### 2. ارسال لینک بازیابی رمز عبور

```python
reset_token = email_service.send_password_reset_email(user, language='fa')
if reset_token:
    print(f"Reset token: {reset_token.token}")
```

### 3. ارسال تایید خرید

```python
email_service.send_purchase_confirmation(
    user=user,
    plan_name='Premium Monthly',
    amount=99000,
    language='fa'
)
```

### 4. ارسال یادآوری انقضا (خودکار توسط Celery)

```python
# این task‌ها به صورت خودکار اجرا می‌شوند
# اما می‌توانید دستی هم اجرا کنید:
from apps.accounts.tasks import check_subscription_expiry

check_subscription_expiry.delay()
```

### 5. ارسال تخفیف به همه کاربران

```python
from apps.accounts.tasks import bulk_send_discount_offer

bulk_send_discount_offer.delay(
    discount_code='SUMMER2024',
    discount_percent=30,
    language='fa'
)
```

---

## عیب‌یابی

### خطای "Authentication failed"

- مطمئن شوید 2-Step Verification فعال است
- App Password را صحیح کپی کرده‌اید (بدون فاصله)
- ایمیل Gmail درست است

### خطای "SMTPAuthenticationError"

```python
# تست اتصال SMTP
import smtplib

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your-email@gmail.com', 'your-app-password')
    print("✅ SMTP connection successful!")
    server.quit()
except Exception as e:
    print(f"❌ SMTP connection failed: {e}")
```

### ایمیل‌ها به Spam می‌روند

1. SPF Record اضافه کنید (اگر دامنه شخصی دارید)
2. از ایمیل تایید شده استفاده کنید
3. محتوای ایمیل را بهینه کنید (کمتر از لینک‌های مشکوک استفاده کنید)

---

## امنیت

⚠️ **هرگز App Password یا credentials را در Git commit نکنید!**

```bash
# اضافه کردن به .gitignore
.env
config/gmail_credentials.json
config/gmail_token.json
*.pyc
__pycache__/
```

---

## لینک‌های مفید

- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [App Passwords](https://myaccount.google.com/apppasswords)
- [Celery Documentation](https://docs.celeryproject.org/)

---

**تاریخ:** 2025-12-22  
**نسخه:** 1.0
