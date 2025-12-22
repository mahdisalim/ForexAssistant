# خلاصه روزانه بازار - Daily Market Summary

## 📋 توضیحات

این ویژگی به صورت خودکار:
1. **از 5 منبع خبری معتبر** اخبار را جمع‌آوری می‌کند:
   - Investing.com
   - ForexFactory
   - DailyFX
   - FXStreet
   - ForexLive

2. **با استفاده از هوش مصنوعی** خلاصه جامعی تولید می‌کند شامل:
   - خلاصه بازار
   - تحلیل اقتصادی
   - تحلیل سیاسی
   - وضعیت بازارهای مالی
   - تیترهای مهم
   - رویدادهای پیش رو
   - حال و هوای بازار

## 🚀 نحوه استفاده

### از API:

```bash
# خلاصه به زبان فارسی
curl "http://localhost:8000/api/summary/?timeframe=H1&asset=USD&lang=fa"

# خلاصه به زبان انگلیسی
curl "http://localhost:8000/api/summary/?timeframe=H1&asset=EUR&lang=en"

# خلاصه به زبان عربی
curl "http://localhost:8000/api/summary/?timeframe=D1&asset=GBP&lang=ar"
```

### پارامترها:

| پارامتر | توضیحات | مقادیر ممکن | پیش‌فرض |
|---------|---------|-------------|---------|
| `timeframe` | بازه زمانی تحلیل | M1, M5, M15, M30, H1, H4, D1, W1 | H1 |
| `asset` | دارایی مورد نظر | USD, EUR, GBP, JPY, XAU, BTC, ... | USD |
| `lang` | زبان خلاصه | fa, en, ar, tr, de, fr, es, ru, zh, ja, ko, pt, it, hi | fa |

### دارایی‌های پشتیبانی شده:

**ارزها:**
- USD (دلار آمریکا)
- EUR (یورو)
- GBP (پوند انگلیس)
- JPY (ین ژاپن)
- CHF (فرانک سوئیس)
- AUD (دلار استرالیا)
- CAD (دلار کانادا)
- NZD (دلار نیوزیلند)
- CNY (یوان چین)

**کالاها:**
- XAU (طلا)
- XAG (نقره)
- OIL (نفت)

**شاخص‌ها:**
- SPX (S&P 500)
- DJI (Dow Jones)
- NDX (NASDAQ)

**رمزارزها:**
- BTC (بیت‌کوین)
- ETH (اتریوم)
- و سایر رمزارزهای اصلی

## 📊 نمونه پاسخ:

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
  "summary": "**خلاصه بازار**: دلار آمریکا امروز...",
  "success": true
}
```

## ⚙️ تنظیمات

برای استفاده از این ویژگی، باید کلید API OpenAI را در فایل `.env` تنظیم کنید:

```bash
OPENAI_API_KEY=your-api-key-here
```

## 🔄 اجرای دستی Scraping

اگر می‌خواهید به صورت دستی اخبار را جمع‌آوری کنید:

```bash
# وارد کانتینر شوید
docker compose -f /srv/deploy/docker-compose.yml exec web bash

# اجرای scraper
python -c "
import asyncio
from scrapers.scraper_manager import ScraperManager
from pathlib import Path

async def main():
    manager = ScraperManager(Path('/app/data'))
    articles = await manager.scrape_all()
    print(f'Scraped {len(articles)} articles')

asyncio.run(main())
"
```

## 📝 نکات مهم

1. **زمان پاسخ**: اولین بار که این endpoint را فراخوانی می‌کنید، ممکن است 30-60 ثانیه طول بکشد چون باید از 5 منبع اخبار را جمع‌آوری کند.

2. **Cache**: برای بهبود عملکرد، می‌توانید نتایج را cache کنید.

3. **Rate Limiting**: برخی از سایت‌های خبری ممکن است محدودیت تعداد درخواست داشته باشند.

4. **زبان‌های پشتیبانی شده**: سیستم از 14 زبان مختلف پشتیبانی می‌کند.

## 🐛 عیب‌یابی

اگر خطا دریافت کردید:

1. **بررسی لاگ‌ها:**
```bash
docker compose -f /srv/deploy/docker-compose.yml logs web --tail 100
```

2. **بررسی کلید OpenAI:**
```bash
docker compose -f /srv/deploy/docker-compose.yml exec web env | grep OPENAI
```

3. **تست دستی scraper:**
```bash
docker compose -f /srv/deploy/docker-compose.yml exec web python -c "
from scrapers.investing_scraper import InvestingScraper
import asyncio
scraper = InvestingScraper()
articles = asyncio.run(scraper.scrape_news())
print(f'Found {len(articles)} articles')
"
```

## 🔮 توسعه آینده

- [ ] Cache کردن نتایج برای بهبود سرعت
- [ ] اضافه کردن منابع خبری بیشتر
- [ ] پشتیبانی از تحلیل تکنیکال همراه با اخبار
- [ ] ارسال خلاصه روزانه به ایمیل
- [ ] نمودارهای تعاملی
