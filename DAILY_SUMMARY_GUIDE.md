# 📊 راهنمای استفاده از خلاصه روزانه بازار

## ✅ بخش خلاصه روزانه کامل شد!

سیستم خلاصه روزانه بازار به طور کامل پیاده‌سازی شده و آماده استفاده است.

---

## 🎯 قابلیت‌ها

### 1️⃣ جمع‌آوری خودکار اخبار از 5 منبع معتبر:
- **Investing.com** - اخبار جهانی بازارهای مالی
- **ForexFactory** - تقویم اقتصادی و اخبار فارکس
- **DailyFX** - تحلیل‌های تخصصی
- **FXStreet** - اخبار و تحلیل‌های فنی
- **ForexLive** - اخبار لحظه‌ای بازار

### 2️⃣ تحلیل هوشمند با AI:
سیستم با استفاده از OpenAI، خلاصه‌ای جامع تولید می‌کند که شامل:
- **خلاصه بازار**: نمای کلی از وضعیت بازار
- **تحلیل اقتصادی**: بررسی داده‌های اقتصادی مهم
- **تحلیل سیاسی**: تأثیر رویدادهای سیاسی
- **وضعیت بازارهای مالی**: بررسی سهام، ارز، طلا و...
- **تیترهای مهم**: خبرهای برجسته روز
- **رویدادهای پیش رو**: تقویم اقتصادی
- **حال و هوای بازار**: احساسات و روند کلی

### 3️⃣ پشتیبانی از 14 زبان:
فارسی، انگلیسی، عربی، ترکی، آلمانی، فرانسوی، اسپانیایی، روسی، چینی، ژاپنی، کره‌ای، پرتغالی، ایتالیایی، هندی

---

## 🚀 نحوه استفاده

### از مرورگر:

```
http://localhost:8000/api/summary/?timeframe=H1&asset=USD&lang=fa
```

### از JavaScript:

```javascript
async function getDailySummary() {
    const response = await fetch(
        'http://localhost:8000/api/summary/?timeframe=H1&asset=USD&lang=fa'
    );
    const data = await response.json();
    
    console.log('تعداد اخبار:', data.articles_count);
    console.log('منابع:', data.sources);
    console.log('خلاصه:', data.summary);
}

getDailySummary();
```

### از Python:

```python
import requests

response = requests.get(
    'http://localhost:8000/api/summary/',
    params={
        'timeframe': 'H1',
        'asset': 'USD',
        'lang': 'fa'
    }
)

data = response.json()
print(f"تعداد اخبار: {data['articles_count']}")
print(f"خلاصه:\n{data['summary']}")
```

---

## 📝 پارامترها

### timeframe (بازه زمانی):
- `M1`, `M5`, `M15`, `M30` - برای اسکالپینگ
- `H1`, `H4` - برای معاملات روزانه
- `D1`, `W1` - برای سوئینگ تریدینگ

### asset (دارایی):

**ارزها:**
- `USD` - دلار آمریکا 🇺🇸
- `EUR` - یورو 🇪🇺
- `GBP` - پوند انگلیس 🇬🇧
- `JPY` - ین ژاپن 🇯🇵
- `CHF` - فرانک سوئیس 🇨🇭
- `AUD` - دلار استرالیا 🇦🇺
- `CAD` - دلار کانادا 🇨🇦
- `NZD` - دلار نیوزیلند 🇳🇿

**کالاها:**
- `XAU` - طلا 🥇
- `XAG` - نقره 🥈
- `OIL` - نفت 🛢️

**شاخص‌ها:**
- `SPX` - S&P 500
- `DJI` - Dow Jones
- `NDX` - NASDAQ

**رمزارزها:**
- `BTC` - بیت‌کوین ₿
- `ETH` - اتریوم
- `BNB` - بایننس کوین

### lang (زبان):
- `fa` - فارسی 🇮🇷
- `en` - انگلیسی 🇬🇧
- `ar` - عربی 🇸🇦
- `tr` - ترکی 🇹🇷
- و 10 زبان دیگر...

---

## 💡 مثال‌های کاربردی

### 1. خلاصه بازار دلار به فارسی:
```
http://localhost:8000/api/summary/?asset=USD&lang=fa
```

### 2. تحلیل طلا برای معاملات روزانه:
```
http://localhost:8000/api/summary/?timeframe=H4&asset=XAU&lang=en
```

### 3. وضعیت بیت‌کوین به عربی:
```
http://localhost:8000/api/summary/?timeframe=D1&asset=BTC&lang=ar
```

---

## 📊 نمونه پاسخ

```json
{
  "generated_at": "2025-12-20T16:20:32.185520",
  "articles_count": 45,
  "timeframe": "H1",
  "asset": "USD",
  "lang": "fa",
  "sources": [
    "Investing.com",
    "ForexFactory",
    "DailyFX",
    "FXStreet",
    "ForexLive"
  ],
  "summary": "**خلاصه بازار**\n\nدلار آمریکا در معاملات امروز...\n\n**تحلیل اقتصادی**\n\nداده‌های اشتغال نشان می‌دهد...\n\n**تحلیل سیاسی**\n\nتنش‌های ژئوپلیتیکی...",
  "success": true
}
```

---

## ⚙️ تنظیمات اولیه

### 1. کلید OpenAI را تنظیم کنید:

```bash
# ویرایش فایل .env
nano /srv/deploy/.env

# اضافه کردن کلید
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. راه‌اندازی مجدد:

```bash
cd /srv/deploy
./start.sh restart
```

---

## 🔍 بررسی وضعیت

### تست سریع:
```bash
curl "http://localhost:8000/api/summary/?asset=USD&lang=en"
```

### مشاهده لاگ‌ها:
```bash
cd /srv/deploy
./start.sh logs
```

### بررسی تعداد اخبار جمع‌آوری شده:
```bash
docker compose -f /srv/deploy/docker-compose.yml exec web ls -lh /app/data/
```

---

## ⏱️ زمان پاسخ

- **اولین بار**: 30-60 ثانیه (جمع‌آوری اخبار از 5 منبع)
- **بار دوم**: 10-20 ثانیه (تحلیل AI)

💡 **توصیه**: برای بهبود سرعت، می‌توانید نتایج را در frontend کش کنید.

---

## 🎨 نمایش در رابط کاربری

### مثال HTML/JavaScript:

```html
<div id="market-summary">
  <button onclick="loadSummary()">دریافت خلاصه بازار</button>
  <div id="summary-content"></div>
</div>

<script>
async function loadSummary() {
  const content = document.getElementById('summary-content');
  content.innerHTML = '<p>در حال بارگذاری...</p>';
  
  try {
    const response = await fetch(
      '/api/summary/?timeframe=H1&asset=USD&lang=fa'
    );
    const data = await response.json();
    
    if (data.success) {
      content.innerHTML = `
        <div class="summary-box">
          <h3>خلاصه بازار - ${data.asset}</h3>
          <p><strong>تعداد اخبار:</strong> ${data.articles_count}</p>
          <p><strong>منابع:</strong> ${data.sources.join(', ')}</p>
          <div class="summary-text">${formatSummary(data.summary)}</div>
        </div>
      `;
    }
  } catch (error) {
    content.innerHTML = '<p>خطا در دریافت اطلاعات</p>';
  }
}

function formatSummary(text) {
  // تبدیل markdown به HTML
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}
</script>
```

---

## 🐛 عیب‌یابی

### مشکل: "No news articles found"

**راه‌حل:**
```bash
# اجرای دستی scraper
docker compose -f /srv/deploy/docker-compose.yml exec web python -c "
import asyncio
from scrapers.scraper_manager import ScraperManager
from pathlib import Path

async def test():
    manager = ScraperManager(Path('/app/data'))
    articles = await manager.scrape_all()
    print(f'✓ جمع‌آوری {len(articles)} خبر')
    for article in articles[:5]:
        print(f'  - {article.title}')

asyncio.run(test())
"
```

### مشکل: "Error generating summary"

**بررسی کلید OpenAI:**
```bash
docker compose -f /srv/deploy/docker-compose.yml exec web env | grep OPENAI_API_KEY
```

---

## 📚 مستندات بیشتر

- مستندات کامل: `/srv/apps/analysis/README.md`
- کد منبع: `/srv/apps/analysis/services.py`
- Scrapers: `/srv/scrapers/`
- AI Analyzer: `/srv/llm/analyzer.py`

---

## ✨ ویژگی‌های آینده

- [ ] Cache کردن نتایج (کاهش زمان پاسخ)
- [ ] Webhook برای اطلاع‌رسانی خودکار
- [ ] تحلیل احساسات (Sentiment Analysis)
- [ ] نمودارهای تعاملی
- [ ] ارسال خلاصه به ایمیل/تلگرام

---

## 🎉 تمام!

بخش خلاصه روزانه بازار به طور کامل پیاده‌سازی شده و آماده استفاده است.

**آدرس API:**
```
http://localhost:8000/api/summary/
```

**پارامترهای اصلی:**
- `timeframe`: بازه زمانی (پیش‌فرض: H1)
- `asset`: دارایی (پیش‌فرض: USD)
- `lang`: زبان (پیش‌فرض: fa)

موفق باشید! 🚀
