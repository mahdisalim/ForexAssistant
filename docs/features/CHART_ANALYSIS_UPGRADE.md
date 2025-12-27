# Chart Analysis System Upgrade

## تغییرات اعمال شده

### 1. سیستم انعطاف‌پذیر انتخاب نماد (Flexible Symbol Selection)

#### تغییرات در `models.py`:
- اضافه شدن فیلد `tradingview_symbol` به مدل `CurrencyPair`
- کاربر می‌تواند برای هر جفت ارز، نماد TradingView دلخواه خود را تعیین کند
- Migration ایجاد شده: `0002_currencypair_tradingview_symbol.py`

#### تغییرات در `chart_service.py`:
- **حذف هارد کد `SYMBOL_MAP`**: دیگر نمادها هارد کد نیستند
- **منطق Database + Fallback هوشمند**:
  1. ابتدا از دیتابیس چک می‌کند
  2. اگر نبود، از الگوریتم تشخیص هوشمند استفاده می‌کند
  3. پشتیبانی خودکار از:
     - جفت ارزهای فارکس (FX:)
     - طلا و نقره (TVC:)
     - ارزهای دیجیتال (BITSTAMP:)
     - شاخص‌ها (SP:, DJ:, NASDAQ:)
     - کالاها (TVC:)

**مثال استفاده:**
```python
# در Django Admin یا از طریق API
pair = CurrencyPair.objects.get(symbol='EURUSD')
pair.tradingview_symbol = 'FX:EURUSD'  # یا هر نماد دلخواه دیگر
pair.save()
```

### 2. سیستم Multi-Timeframe Analysis

#### متد جدید در `chart_service.py`:
```python
async def capture_multi_timeframe_charts(
    pair: str,
    timeframes: list = None,
    trading_style: str = 'day'
) -> Dict[str, Optional[str]]
```

**ویژگی‌ها:**
- گرفتن خودکار چند تایم‌فریم بر اساس trading style:
  - `scalp`: M5, M15, H1
  - `day`: H1, H4, D1
  - `swing`: H4, D1, W1
  - `position`: D1, W1, MN1
- یا تعیین دستی تایم‌فریم‌های دلخواه
- مدیریت خطا برای هر تایم‌فریم به صورت جداگانه
- لاگ کامل برای debugging

#### متد جدید در `chart_analyzer.py`:
```python
async def analyze_multi_timeframe_charts(
    pair: str,
    chart_images: Dict[str, str],
    trading_style: str = "day"
) -> Dict[str, Any]
```

**ویژگی‌ها:**
- تحلیل همزمان چند تایم‌فریم توسط AI
- بررسی Timeframe Alignment
- شناسایی Confluence Zones
- تحلیل Higher Timeframe Context
- یافتن Entry Points دقیق در Lower Timeframes

#### تغییرات در `services.py`:
```python
async def auto_chart_analysis(
    pair: str,
    timeframe: str = 'H1',
    trading_style: str = 'day',
    multi_timeframe: bool = False,  # جدید
    timeframes: list = None         # جدید
) -> Dict
```

**نحوه استفاده:**

**تک تایم‌فریم (حالت قبلی):**
```python
result = await service.auto_chart_analysis(
    pair='EURUSD',
    timeframe='H1',
    trading_style='day'
)
```

**چند تایم‌فریم (حالت جدید):**
```python
# حالت خودکار
result = await service.auto_chart_analysis(
    pair='EURUSD',
    trading_style='day',
    multi_timeframe=True
)

# حالت دستی
result = await service.auto_chart_analysis(
    pair='EURUSD',
    trading_style='day',
    multi_timeframe=True,
    timeframes=['M15', 'H1', 'H4', 'D1']
)
```

### 3. بهبودهای دیگر

#### بهبود Playwright Screenshot:
- افزایش viewport به 1400x900
- اضافه شدن `--no-sandbox` برای محیط‌های Docker
- بهبود timeout و wait times
- لاگ بهتر با ایموجی برای راحتی debugging

#### مدیریت خطا:
- Graceful fallback در صورت خرابی هر تایم‌فریم
- ادامه تحلیل با تایم‌فریم‌های موفق
- پیام‌های خطای واضح‌تر

## Migration

برای اعمال تغییرات دیتابیس:

```bash
python manage.py migrate analysis
```

## نمونه Response

### Single Timeframe:
```json
{
  "pair": "EURUSD",
  "timeframe": "H1",
  "trading_style": "day",
  "analysis": {
    "sentiment": "Bullish",
    "sentiment_score": 75,
    "trend": "uptrend",
    "key_factors": ["..."],
    "support_levels": ["1.0850", "1.0820"],
    "resistance_levels": ["1.0920", "1.0950"]
  },
  "recommendation": {
    "recommendation": "BUY",
    "confidence": 75,
    "entry_zone": {"min": "1.0870", "max": "1.0880"},
    "stop_loss": {"price": "1.0840", "pips": 30},
    "take_profit": {"price": "1.0940", "pips": 60}
  }
}
```

### Multi-Timeframe:
```json
{
  "pair": "EURUSD",
  "timeframes": ["H1", "H4", "D1"],
  "trading_style": "day",
  "analysis": {
    "sentiment": "Bullish",
    "alignment": "aligned",
    "timeframe_analysis": {
      "H1": "Strong bullish momentum...",
      "H4": "Breaking resistance...",
      "D1": "Uptrend confirmed..."
    },
    "timeframe_confluence": "All timeframes show bullish alignment..."
  },
  "recommendation": {
    "recommendation": "BUY",
    "confidence": 85,
    "timeframes": ["H1", "H4", "D1"]
  }
}
```

## Backward Compatibility

✅ تمام کدهای قبلی بدون تغییر کار می‌کنند
✅ اگر `multi_timeframe=False` (default)، رفتار دقیقاً مثل قبل است
✅ نمادهای قدیمی با الگوریتم fallback شناسایی می‌شوند

## نکات مهم

1. **Playwright**: اطمینان حاصل کنید Playwright نصب است:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **OpenAI API**: برای multi-timeframe analysis، مصرف token بیشتر است (چند تصویر)

3. **Performance**: multi-timeframe کندتر است (چند screenshot + تحلیل پیچیده‌تر)

4. **Database**: حتماً migration را اجرا کنید

## Testing

```python
# تست single timeframe
result = await service.auto_chart_analysis('EURUSD', 'H1', 'day')

# تست multi-timeframe
result = await service.auto_chart_analysis('EURUSD', trading_style='day', multi_timeframe=True)

# تست نماد سفارشی
pair = CurrencyPair.objects.get(symbol='BTCUSD')
pair.tradingview_symbol = 'COINBASE:BTCUSD'  # به جای BITSTAMP
pair.save()
```

## خلاصه تغییرات فایل‌ها

- ✅ `/srv/apps/analysis/models.py` - اضافه شدن فیلد tradingview_symbol
- ✅ `/srv/apps/analysis/migrations/0002_currencypair_tradingview_symbol.py` - Migration جدید
- ✅ `/srv/apps/analysis/chart_service.py` - حذف هارد کد + multi-timeframe support
- ✅ `/srv/llm/chart_analyzer.py` - متد analyze_multi_timeframe_charts
- ✅ `/srv/apps/analysis/services.py` - پارامترهای multi_timeframe و timeframes

---
**تاریخ:** 2025-12-22
**نسخه:** 2.0
