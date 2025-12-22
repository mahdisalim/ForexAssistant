# سیستم ایمیل و نوتیفیکیشن - خلاصه کامل

## 📋 فهرست مطالب

1. [معرفی](#معرفی)
2. [فایل‌های ایجاد شده](#فایل‌های-ایجاد-شده)
3. [راه‌اندازی سریع](#راه‌اندازی-سریع)
4. [نحوه استفاده](#نحوه-استفاده)
5. [API Reference](#api-reference)
6. [Celery Tasks](#celery-tasks)
7. [Templates](#templates)
8. [عیب‌یابی](#عیب‌یابی)

---

## معرفی

سیستم کامل ایمیل برای ارسال:
- ✅ کد تایید ایمیل (6 رقمی)
- ✅ لینک بازیابی رمز عبور
- ✅ تایید خرید اشتراک
- ✅ یادآوری انقضای اشتراک (10، 5، 3 روز)
- ✅ اطلاع انقضای اشتراک
- ✅ پیشنهادات تخفیف
- ✅ اطلاع‌رسانی رویدادها

**ویژگی‌ها:**
- 🔐 امن و رمزنگاری شده
- 🌐 پشتیبانی از فارسی و انگلیسی
- ⏰ یادآوری‌های خودکار با Celery
- 📊 ردیابی کامل ایمیل‌های ارسال شده
- 🎨 Template‌های زیبا و responsive

---

## فایل‌های ایجاد شده

### 1. Models (`/srv/apps/accounts/models.py`)
```python
- EmailVerification      # کدهای تایید 6 رقمی
- PasswordResetToken     # توکن‌های بازیابی رمز
- EmailNotification      # ردیابی ایمیل‌های ارسال شده
```

### 2. Email Service (`/srv/apps/accounts/email_service.py`)
```python
class EmailService:
    - send_verification_email()           # کد تایید
    - send_password_reset_email()         # بازیابی رمز
    - send_purchase_confirmation()        # تایید خرید
    - send_expiry_warning()               # یادآوری انقضا
    - send_subscription_expired()         # اطلاع انقضا
    - send_discount_offer()               # پیشنهاد تخفیف
    - send_event_notification()           # اطلاع رویداد
```

### 3. Celery Tasks (`/srv/apps/accounts/tasks.py`)
```python
- check_subscription_expiry()         # چک روزانه انقضا
- check_expired_subscriptions()       # چک اشتراک‌های منقضی شده
- send_verification_email_task()      # ارسال async کد تایید
- send_password_reset_task()          # ارسال async بازیابی رمز
- bulk_send_discount_offer()          # ارسال گروهی تخفیف
- bulk_send_event_notification()      # ارسال گروهی رویداد
```

### 4. Email Templates (`/srv/templates/emails/`)
```
✅ verification_fa.html              # کد تایید فارسی
✅ verification_en.html              # کد تایید انگلیسی
✅ password_reset_fa.html            # بازیابی رمز فارسی
✅ password_reset_en.html            # بازیابی رمز انگلیسی
✅ expiry_warning_fa.html            # یادآوری انقضا
✅ purchase_confirmation_fa.html     # تایید خرید
✅ subscription_expired_fa.html      # اطلاع انقضا
✅ discount_offer_fa.html            # پیشنهاد تخفیف
✅ event_notification_fa.html        # اطلاع رویداد
```

### 5. Configuration
```
✅ /srv/config/settings.py          # تنظیمات ایمیل و Celery
✅ /srv/config/celery.py             # پیکربندی Celery
✅ /srv/.env.example                 # نمونه متغیرهای محیطی
```

### 6. Migrations
```
✅ /srv/apps/accounts/migrations/0002_email_notifications.py
```

### 7. Documentation
```
✅ /srv/GMAIL_SETUP_GUIDE.md        # راهنمای کامل Gmail
✅ /srv/EMAIL_SYSTEM_README.md      # این فایل
```

---

## راه‌اندازی سریع

### مرحله 1: نصب Dependencies

```bash
# اگر قبلاً نصب نکرده‌اید
pip install redis celery django-celery-beat django-celery-results
```

### مرحله 2: دریافت Gmail App Password

1. به [Google Account Security](https://myaccount.google.com/security) بروید
2. **2-Step Verification** را فعال کنید
3. به [App Passwords](https://myaccount.google.com/apppasswords) بروید
4. یک App Password جدید بسازید
5. رمز 16 رقمی را کپی کنید

### مرحله 3: پیکربندی `.env`

```bash
# کپی کردن .env.example
cp .env.example .env

# ویرایش .env
nano .env
```

اضافه کنید:
```env
# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # App Password
DEFAULT_FROM_EMAIL=your-email@gmail.com
EMAIL_FROM_NAME=Forex Assistant
FRONTEND_URL=http://localhost:3000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### مرحله 4: اجرای Migration

```bash
python manage.py migrate accounts
```

### مرحله 5: راه‌اندازی Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# یا به صورت دستی
redis-server
```

### مرحله 6: راه‌اندازی Celery

```bash
# Terminal 1: Celery Worker
celery -A config worker -l info

# Terminal 2: Celery Beat (برای task‌های زمان‌بندی شده)
celery -A config beat -l info
```

### مرحله 7: تست

```python
from apps.accounts.email_service import get_email_service
from apps.accounts.models import User

user = User.objects.first()
email_service = get_email_service()

# تست ارسال کد تایید
verification = email_service.send_verification_email(user, language='fa')
print(f"✅ Verification code sent: {verification.code if verification else 'Failed'}")
```

---

## نحوه استفاده

### 1. ارسال کد تایید ایمیل

```python
from apps.accounts.email_service import get_email_service

email_service = get_email_service()

# ارسال همزمان (Sync)
verification = email_service.send_verification_email(user, language='fa')
if verification:
    print(f"Code: {verification.code}")
    print(f"Expires at: {verification.expires_at}")

# ارسال غیرهمزمان (Async با Celery)
from apps.accounts.tasks import send_verification_email_task
send_verification_email_task.delay(user.id, language='fa')
```

**تایید کد:**
```python
from apps.accounts.models import EmailVerification

code = request.POST.get('code')
verification = EmailVerification.objects.filter(
    user=user,
    code=code,
    is_used=False
).first()

if verification and verification.is_valid():
    verification.is_used = True
    verification.save()
    # کد معتبر است
else:
    # کد نامعتبر یا منقضی شده
```

### 2. بازیابی رمز عبور

```python
# ارسال لینک بازیابی
reset_token = email_service.send_password_reset_email(user, language='fa')

# یا با Celery
from apps.accounts.tasks import send_password_reset_task
send_password_reset_task.delay(user.id, language='fa')
```

**تایید توکن:**
```python
from apps.accounts.models import PasswordResetToken

token = request.GET.get('token')
reset = PasswordResetToken.objects.filter(
    token=token,
    is_used=False
).first()

if reset and reset.is_valid():
    # توکن معتبر - اجازه تغییر رمز
    reset.is_used = True
    reset.save()
    user = reset.user
    user.set_password(new_password)
    user.save()
```

### 3. تایید خرید

```python
# بعد از پرداخت موفق
email_service.send_purchase_confirmation(
    user=user,
    plan_name='Premium Monthly',
    amount=99000,  # تومان
    language='fa'
)

# یا با Celery
from apps.accounts.tasks import send_purchase_confirmation_task
send_purchase_confirmation_task.delay(
    user_id=user.id,
    plan_name='Premium Monthly',
    amount=99000,
    language='fa'
)
```

### 4. یادآوری انقضای اشتراک (خودکار)

```python
# این task‌ها به صورت خودکار توسط Celery Beat اجرا می‌شوند
# هر روز ساعت 9 صبح چک می‌شود

# اما می‌توانید دستی هم اجرا کنید:
from apps.accounts.tasks import check_subscription_expiry
check_subscription_expiry.delay()
```

**منطق:**
- اگر 10 روز تا انقضا مانده باشد → ایمیل یادآوری
- اگر 5 روز تا انقضا مانده باشد → ایمیل یادآوری
- اگر 3 روز تا انقضا مانده باشد → ایمیل یادآوری
- اگر اشتراک منقضی شد → ایمیل اطلاع + تبدیل به Free

### 5. ارسال تخفیف

```python
# ارسال به یک کاربر
email_service.send_discount_offer(
    user=user,
    discount_code='SUMMER2024',
    discount_percent=30,
    language='fa'
)

# ارسال به همه کاربران (Bulk)
from apps.accounts.tasks import bulk_send_discount_offer
bulk_send_discount_offer.delay(
    discount_code='SUMMER2024',
    discount_percent=30,
    language='fa'
)
```

### 6. اطلاع رویداد

```python
# ارسال به یک کاربر
email_service.send_event_notification(
    user=user,
    event_title='وبینار رایگان تحلیل تکنیکال',
    event_description='یکشنبه ساعت 20:00 - ثبت‌نام رایگان',
    language='fa'
)

# ارسال به همه کاربران
from apps.accounts.tasks import bulk_send_event_notification
bulk_send_event_notification.delay(
    event_title='وبینار رایگان تحلیل تکنیکال',
    event_description='یکشنبه ساعت 20:00 - ثبت‌نام رایگان',
    language='fa'
)
```

---

## API Reference

### EmailService Methods

#### `send_verification_email(user, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `language`: 'fa' یا 'en'
- **خروجی:** EmailVerification instance یا None
- **کد اعتبار:** 15 دقیقه

#### `send_password_reset_email(user, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `language`: 'fa' یا 'en'
- **خروجی:** PasswordResetToken instance یا None
- **توکن اعتبار:** 1 ساعت

#### `send_purchase_confirmation(user, plan_name, amount, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `plan_name`: نام پلن (str)
  - `amount`: مبلغ (float)
  - `language`: 'fa' یا 'en'
- **خروجی:** bool

#### `send_expiry_warning(user, days_left, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `days_left`: 10، 5 یا 3
  - `language`: 'fa' یا 'en'
- **خروجی:** bool

#### `send_subscription_expired(user, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `language`: 'fa' یا 'en'
- **خروجی:** bool

#### `send_discount_offer(user, discount_code, discount_percent, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `discount_code`: کد تخفیف (str)
  - `discount_percent`: درصد تخفیف (int)
  - `language`: 'fa' یا 'en'
- **خروجی:** bool

#### `send_event_notification(user, event_title, event_description, language='fa')`
- **پارامترها:**
  - `user`: User instance
  - `event_title`: عنوان رویداد (str)
  - `event_description`: توضیحات (str)
  - `language`: 'fa' یا 'en'
- **خروجی:** bool

---

## Celery Tasks

### Periodic Tasks (خودکار)

#### `check_subscription_expiry`
- **زمان اجرا:** هر روز ساعت 9:00 صبح
- **عملکرد:** چک کردن اشتراک‌ها و ارسال یادآوری 10، 5، 3 روز

#### `check_expired_subscriptions`
- **زمان اجرا:** هر روز ساعت 10:00 صبح
- **عملکرد:** چک کردن اشتراک‌های منقضی شده و تبدیل به Free

### Async Tasks (دستی)

#### `send_verification_email_task(user_id, language='fa')`
```python
from apps.accounts.tasks import send_verification_email_task
send_verification_email_task.delay(user.id, 'fa')
```

#### `send_password_reset_task(user_id, language='fa')`
```python
from apps.accounts.tasks import send_password_reset_task
send_password_reset_task.delay(user.id, 'fa')
```

#### `send_purchase_confirmation_task(user_id, plan_name, amount, language='fa')`
```python
from apps.accounts.tasks import send_purchase_confirmation_task
send_purchase_confirmation_task.delay(user.id, 'Premium', 99000, 'fa')
```

#### `bulk_send_discount_offer(discount_code, discount_percent, language='fa')`
```python
from apps.accounts.tasks import bulk_send_discount_offer
bulk_send_discount_offer.delay('SUMMER30', 30, 'fa')
```

#### `bulk_send_event_notification(event_title, event_description, language='fa')`
```python
from apps.accounts.tasks import bulk_send_event_notification
bulk_send_event_notification.delay('وبینار', 'توضیحات', 'fa')
```

---

## Templates

تمام template‌ها در `/srv/templates/emails/` قرار دارند.

### ساختار Template

```html
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <style>
        /* Inline CSS for email compatibility */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <!-- Header -->
        </div>
        <div class="content">
            <!-- محتوای اصلی -->
            {{ user.get_full_name }}
            {{ code }}
            {{ site_name }}
        </div>
        <div class="footer">
            <!-- Footer -->
        </div>
    </div>
</body>
</html>
```

### Context Variables

هر template دسترسی به این متغیرها دارد:
- `user`: User instance
- `site_name`: نام سایت
- `code`: کد تایید (در verification)
- `reset_url`: لینک بازیابی (در password reset)
- `expires_minutes` / `expires_hours`: زمان انقضا
- `days_left`: روزهای باقیمانده (در expiry warning)
- `discount_code`: کد تخفیف
- `discount_percent`: درصد تخفیف
- و غیره...

---

## عیب‌یابی

### ❌ خطا: "SMTPAuthenticationError"

**علت:** App Password اشتباه یا 2-Step Verification فعال نیست

**راه‌حل:**
1. مطمئن شوید 2-Step Verification فعال است
2. App Password جدید بسازید
3. رمز را بدون فاصله کپی کنید
4. `.env` را ذخیره کنید و سرور را restart کنید

### ❌ خطا: "Connection refused" (Redis)

**علت:** Redis در حال اجرا نیست

**راه‌حل:**
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis

# یا دستی
redis-server
```

### ❌ ایمیل‌ها به Spam می‌روند

**راه‌حل:**
1. از ایمیل تایید شده استفاده کنید
2. محتوای ایمیل را بهینه کنید
3. SPF/DKIM record اضافه کنید (برای دامنه شخصی)
4. از لینک‌های مشکوک استفاده نکنید

### ❌ Celery Beat کار نمی‌کند

**راه‌حل:**
```bash
# مطمئن شوید هر دو worker و beat در حال اجرا هستند
celery -A config worker -l info
celery -A config beat -l info

# چک کردن schedule
celery -A config inspect scheduled
```

### ❌ Template پیدا نمی‌شود

**راه‌حل:**
```python
# در settings.py مطمئن شوید TEMPLATES درست است
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # این خط مهم است
        ...
    },
]
```

### 🔍 تست اتصال SMTP

```python
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

---

## مثال‌های کاربردی

### مثال 1: فرآیند ثبت‌نام کامل

```python
from django.contrib.auth import get_user_model
from apps.accounts.email_service import get_email_service

User = get_user_model()

# 1. ایجاد کاربر
user = User.objects.create_user(
    email='user@example.com',
    password='secure_password',
    name='John Doe'
)

# 2. ارسال کد تایید
email_service = get_email_service()
verification = email_service.send_verification_email(user, language='fa')

# 3. کاربر کد را وارد می‌کند
# ... در view دیگر ...

# 4. تایید کد
if verification and verification.is_valid():
    verification.is_used = True
    verification.save()
    user.is_active = True  # یا هر فیلد دیگری
    user.save()
```

### مثال 2: فرآیند خرید اشتراک

```python
from datetime import timedelta
from django.utils import timezone

# 1. پردازش پرداخت
# ... payment processing ...

# 2. بروزرسانی اشتراک کاربر
user.subscription_plan = 'premium'
user.subscription_expires = timezone.now() + timedelta(days=30)
user.save()

# 3. ارسال ایمیل تایید خرید
email_service.send_purchase_confirmation(
    user=user,
    plan_name='Premium Monthly',
    amount=99000,
    language='fa'
)
```

### مثال 3: کمپین تخفیف

```python
from apps.accounts.tasks import bulk_send_discount_offer

# ارسال تخفیف 30% به همه کاربران
bulk_send_discount_offer.delay(
    discount_code='NEWYEAR2025',
    discount_percent=30,
    language='fa'
)
```

---

## امنیت

### ⚠️ نکات مهم امنیتی

1. **هرگز credentials را commit نکنید**
```bash
# .gitignore
.env
*.pyc
__pycache__/
config/gmail_credentials.json
config/gmail_token.json
```

2. **استفاده از Environment Variables**
```python
# ❌ اشتباه
EMAIL_HOST_PASSWORD = 'my-password'

# ✅ درست
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

3. **Rate Limiting**
```python
# محدود کردن تعداد ایمیل‌های ارسالی
from django.core.cache import cache

key = f'email_limit_{user.id}'
count = cache.get(key, 0)
if count >= 5:  # حداکثر 5 ایمیل در ساعت
    raise Exception('Too many emails sent')
cache.set(key, count + 1, 3600)  # 1 ساعت
```

4. **تایید توکن‌ها**
```python
# همیشه is_valid() را چک کنید
if token and token.is_valid() and not token.is_used:
    # OK
else:
    # Invalid or expired
```

---

## مانیتورینگ

### بررسی ایمیل‌های ارسال شده

```python
from apps.accounts.models import EmailNotification

# تمام ایمیل‌های ارسال شده امروز
today_emails = EmailNotification.objects.filter(
    sent_at__date=timezone.now().date()
)

# ایمیل‌های ناموفق
failed_emails = EmailNotification.objects.filter(
    is_successful=False
)

# آمار به تفکیک نوع
from django.db.models import Count
stats = EmailNotification.objects.values('notification_type').annotate(
    count=Count('id'),
    success_count=Count('id', filter=models.Q(is_successful=True))
)
```

### Django Admin

تمام مدل‌ها در Django Admin قابل مشاهده هستند:
- `/admin/accounts/emailverification/`
- `/admin/accounts/passwordresettoken/`
- `/admin/accounts/emailnotification/`

---

## لینک‌های مفید

- 📖 [راهنمای کامل Gmail Setup](./GMAIL_SETUP_GUIDE.md)
- 🔗 [Google App Passwords](https://myaccount.google.com/apppasswords)
- 🔗 [Celery Documentation](https://docs.celeryproject.org/)
- 🔗 [Django Email Backend](https://docs.djangoproject.com/en/stable/topics/email/)
- 🔗 [Redis Documentation](https://redis.io/documentation)

---

## پشتیبانی

اگر مشکلی داشتید:
1. ابتدا بخش [عیب‌یابی](#عیب‌یابی) را بخوانید
2. لاگ‌های Celery و Django را بررسی کنید
3. تست اتصال SMTP را اجرا کنید
4. مطمئن شوید Redis در حال اجرا است

---

**تاریخ:** 2025-12-22  
**نسخه:** 1.0  
**نویسنده:** Forex Assistant Development Team

✅ **سیستم آماده استفاده است!**
