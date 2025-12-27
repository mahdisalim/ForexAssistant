# 🖥️ راهنمای نصب روی Windows VPS

## پیش‌نیازها

- Windows Server 2019/2022 یا Windows 10/11
- Python 3.10+ (توصیه: 3.11)
- MetaTrader 5
- حداقل 2GB RAM
- اتصال اینترنت پایدار
- دسترسی به PyPI (یا VPN در صورت محدودیت)

---

## مراحل نصب

### 1. نصب خودکار

PowerShell را به عنوان Administrator باز کنید و اجرا کنید:

```powershell
# به پوشه پروژه بروید
cd <مسیر-پروژه>

# اجازه اجرای اسکریپت
Set-ExecutionPolicy Bypass -Scope Process -Force

# اجرای نصب
.\deploy\install_windows.ps1
```

> ⚠️ **نکته:** اسکریپت نصب به صورت خودکار:
> - Python را نصب می‌کند (اگر نباشد)
> - محیط مجازی (venv) ایجاد می‌کند
> - وابستگی‌ها را نصب می‌کند
> - فایل `.env` را از `.env.example` کپی می‌کند
> - Task Scheduler را تنظیم می‌کند

### 2. نصب دستی

#### الف) نصب Python
```powershell
winget install Python.Python.3.11
```

#### ب) نصب MetaTrader 5
از سایت بروکر خود دانلود و نصب کنید.

#### ج) نصب وابستگی‌ها
```powershell
# به پوشه پروژه بروید (هرجا که فایل‌ها را قرار داده‌اید)
cd <مسیر-پروژه>

# ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی
.\venv\Scripts\Activate.ps1

# نصب وابستگی‌ها
pip install -r requirements.txt
```

> 💡 **اگر PyPI مسدود است:**
> ```powershell
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
> ```
> یا از VPN استفاده کنید.

#### د) ایجاد فایل تنظیمات
```powershell
copy .env.example .env
# سپس فایل .env را ویرایش کنید
```

---

## پیکربندی

### فایل `.env`

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# MetaTrader 5
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server

# Trading Settings
ACCOUNT_BALANCE=10000
RISK_PERCENT=1.0
MIN_CONFIDENCE=60
DEMO_MODE=true

# Server
HOST=0.0.0.0
PORT=8000
```

### تنظیمات MetaTrader 5

1. MT5 را باز کنید
2. به حساب خود لاگین کنید
3. در Tools > Options > Expert Advisors:
   - ✅ Allow automated trading
   - ✅ Allow DLL imports
4. در Tools > Options > API:
   - ✅ Enable Python API

---

## اجرا

### روش 1: اجرای ساده (توصیه شده)
```powershell
# از پوشه پروژه
.\deploy\start_all.bat
```

### روش 2: اجرای دستی

```powershell
# ابتدا محیط مجازی را فعال کنید
.\venv\Scripts\Activate.ps1

# Terminal 1 - Web Server
python main.py

# Terminal 2 - Trading Bot (در ترمینال جدید)
python trading_bot.py

# Terminal 3 - Monitor (اختیاری)
python deploy\monitor.py
```

> 📌 **مهم:** حتماً قبل از اجرا، محیط مجازی را فعال کنید!

### روش 3: نصب به عنوان Windows Service

```powershell
# با pywin32
pip install pywin32
python deploy\windows_service.py install
python deploy\windows_service.py start

# یا با NSSM
python deploy\windows_service.py nssm
```

---

## پورت‌ها

| سرویس | پورت | آدرس |
|-------|------|------|
| Web Dashboard | 8000 | http://localhost:8000 |
| Monitor | 8080 | http://localhost:8080 |

اگر می‌خواهید از بیرون دسترسی داشته باشید، پورت‌ها را در فایروال باز کنید:

```powershell
New-NetFirewallRule -DisplayName "Forex Web" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Forex Monitor" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow
```

---

## مانیتورینگ

### لاگ‌ها
```
logs/app.log        - لاگ اصلی
logs/service.log    - لاگ سرویس
data/trade_log.json - تاریخچه معاملات
```

### بررسی وضعیت
```powershell
# وضعیت سرویس
Get-Service ForexAssistant

# لاگ‌های اخیر
Get-Content logs\app.log -Tail 50
```

---

## عیب‌یابی

### MT5 متصل نمی‌شود
1. مطمئن شوید MT5 باز است
2. به حساب لاگین کرده‌اید
3. API فعال است (Tools > Options > API)
4. اطلاعات لاگین در `.env` صحیح است

### خطای OpenAI
1. کلید API را بررسی کنید
2. اعتبار حساب OpenAI را چک کنید
3. اتصال اینترنت را تست کنید

### سرویس شروع نمی‌شود
```powershell
# بررسی لاگ
Get-EventLog -LogName Application -Source ForexAssistant -Newest 10

# ری‌استارت
Restart-Service ForexAssistant
```

---

## امنیت

⚠️ **مهم:**

1. فایروال را فعال نگه دارید
2. از رمز عبور قوی برای VPS استفاده کنید
3. پورت‌ها را فقط در صورت نیاز باز کنید
4. ابتدا با `DEMO_MODE=true` تست کنید
5. هرگز بیش از 1-2% ریسک نکنید

---

## پشتیبان‌گیری

```powershell
# پشتیبان‌گیری روزانه (از پوشه پروژه اجرا کنید)
$date = Get-Date -Format "yyyyMMdd"

# ایجاد پوشه backups اگر وجود ندارد
if (-not (Test-Path "backups")) { New-Item -ItemType Directory -Path "backups" }

# فشرده‌سازی
Compress-Archive -Path "data", ".env", "logs" -DestinationPath "backups\forex_$date.zip" -Force
```

---

## به‌روزرسانی

```powershell
# از پوشه پروژه اجرا کنید
git pull

# فعال‌سازی محیط مجازی
.\venv\Scripts\Activate.ps1

# به‌روزرسانی وابستگی‌ها
pip install -r requirements.txt --upgrade

# ری‌استارت سرویس (اگر به عنوان سرویس نصب شده)
Restart-Service ForexAssistant -ErrorAction SilentlyContinue

# یا ری‌استارت دستی
# Ctrl+C برای توقف و دوباره: python main.py
```

---

## ❓ سوالات متداول

### چرا وابستگی‌ها نصب نمی‌شوند؟
احتمالاً PyPI مسدود است. از VPN یا mirror استفاده کنید.

### چرا سایت باز نمی‌شود؟
1. مطمئن شوید سرور در حال اجراست (`python main.py`)
2. آدرس `http://localhost:8000` را باز کنید
3. فایروال را بررسی کنید

### چرا تحلیل کار نمی‌کند؟
1. کلید OpenAI را در `.env` وارد کنید
2. اعتبار حساب OpenAI را بررسی کنید
