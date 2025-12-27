# 📡 API Documentation

**نسخه:** 2.0  
**Base URL:** `http://localhost:8000`  
**تاریخ:** 2025-12-22

---

## 📋 فهرست مطالب

1. [Authentication](#authentication)
2. [Accounts API](#accounts-api)
3. [Analysis API](#analysis-api)
4. [Trading API](#trading-api)
5. [Scraping API](#scraping-api)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)

---

## 🔐 Authentication

### Token-Based Authentication

همه endpoint های محافظت شده نیاز به header زیر دارند:

```http
Authorization: Token your-auth-token-here
```

### دریافت Token

**Endpoint:** `POST /api/auth/signup/` یا `POST /api/auth/signin/`

---

## 👤 Accounts API

### 1. Sign Up (ثبت‌نام)

**Endpoint:** `POST /api/auth/signup/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_plan": "free",
    "subscription_expires": null,
    "is_active": true,
    "date_joined": "2025-12-22T10:30:00Z"
  },
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

**Errors:**
- `400 Bad Request`: Invalid data (email already exists, weak password)

---

### 2. Sign In (ورود)

**Endpoint:** `POST /api/auth/signin/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "remember_me": false
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_plan": "premium",
    "subscription_expires": "2026-01-22T10:30:00Z"
  },
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

**Token Expiry:**
- `remember_me: false` → 7 days
- `remember_me: true` → No expiry

**Errors:**
- `400 Bad Request`: Invalid credentials

---

### 3. Logout (خروج)

**Endpoint:** `POST /api/auth/logout/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request:** Empty body

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

### 4. Get Current User

**Endpoint:** `GET /api/auth/me/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_plan": "premium",
  "subscription_expires": "2026-01-22T10:30:00Z",
  "is_active": true,
  "date_joined": "2025-12-22T10:30:00Z"
}
```

---

### 5. Health Check

**Endpoint:** `GET /api/health/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-22T10:30:00Z"
}
```

---

## 📊 Analysis API

### 1. List Currency Pairs

**Endpoint:** `GET /api/pairs/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Response (200 OK):**
```json
{
  "pairs": {
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
}
```

---

### 2. Add Currency Pair

**Endpoint:** `POST /api/pairs/add/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Request Body:**
```json
{
  "pair": "GBPUSD",
  "config": {
    "volatility": "high",
    "default_sl_pips": 40,
    "default_tp_pips": 80,
    "keywords": ["GBP", "pound", "sterling", "BOE"]
  }
}
```

**Response (201 Created):**
```json
{
  "message": "Pair GBPUSD added successfully",
  "pair": "GBPUSD",
  "config": {
    "volatility": "high",
    "default_sl_pips": 40,
    "default_tp_pips": 80,
    "keywords": ["GBP", "pound", "sterling", "BOE"]
  }
}
```

**Errors:**
- `400 Bad Request`: Pair already exists

---

### 3. Remove Currency Pair

**Endpoint:** `DELETE /api/pairs/{pair}/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Example:** `DELETE /api/pairs/GBPUSD/`

**Response (200 OK):**
```json
{
  "message": "Pair GBPUSD removed successfully"
}
```

**Errors:**
- `404 Not Found`: Pair doesn't exist

---

### 4. Get Analysis for Pair

**Endpoint:** `GET /api/analysis/{pair}/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Query Parameters:**
- `timeframe` (optional): M1, M5, M15, M30, H1, H4, D1, W1 (default: H1)
- `trading_style` (optional): scalp, day, swing, position (default: day)

**Example:** `GET /api/analysis/EURUSD/?timeframe=H4&trading_style=day`

**Response (200 OK):**
```json
{
  "pair": "EURUSD",
  "timeframe": "H4",
  "trading_style": "day",
  "analysis": {
    "sentiment": "Bullish",
    "sentiment_score": 75,
    "trend": "uptrend",
    "key_factors": [
      "Strong bullish momentum on H4",
      "Breaking above resistance at 1.0920",
      "Positive economic data from Eurozone"
    ],
    "support_levels": ["1.0850", "1.0820", "1.0800"],
    "resistance_levels": ["1.0920", "1.0950", "1.0980"],
    "technical_indicators": {
      "RSI": "65 (Bullish)",
      "MACD": "Bullish crossover",
      "Moving_Averages": "Price above 50 and 200 MA"
    }
  },
  "recommendation": {
    "recommendation": "BUY",
    "confidence": 75,
    "entry_zone": {
      "min": "1.0870",
      "max": "1.0880"
    },
    "stop_loss": {
      "price": "1.0840",
      "pips": 30,
      "description": "Below recent swing low"
    },
    "take_profit": {
      "price": "1.0940",
      "pips": 60,
      "description": "At resistance level"
    },
    "risk_reward_ratio": 2.0,
    "timeframe": "H4",
    "reasoning": "Strong bullish momentum with clear support/resistance levels..."
  },
  "generated_at": "2025-12-22T10:30:00Z"
}
```

**Errors:**
- `404 Not Found`: Pair not configured
- `500 Internal Server Error`: Analysis generation failed

---

### 5. Get Analysis for All Pairs

**Endpoint:** `GET /api/analysis/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Query Parameters:**
- `timeframe` (optional): default H1
- `trading_style` (optional): default day

**Response (200 OK):**
```json
{
  "timeframe": "H1",
  "trading_style": "day",
  "results": [
    {
      "pair": "EURUSD",
      "sentiment": "Bullish",
      "recommendation": "BUY",
      "confidence": 75
    },
    {
      "pair": "XAUUSD",
      "sentiment": "Bearish",
      "recommendation": "SELL",
      "confidence": 68
    }
  ],
  "generated_at": "2025-12-22T10:30:00Z"
}
```

**⚠️ Note:** این endpoint فعلاً placeholder است و نیاز به پیاده‌سازی کامل دارد.

---

### 6. Daily Market Summary

**Endpoint:** `GET /api/summary/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Query Parameters:**
- `timeframe` (optional): M1-W1 (default: H1)
- `asset` (optional): USD, EUR, GBP, JPY, XAU, BTC, etc. (default: USD)
- `lang` (optional): fa, en, ar, tr, de, fr, es, ru, zh, ja, ko, pt, it, hi (default: fa)

**Example:** `GET /api/summary/?timeframe=H4&asset=XAU&lang=fa`

**Response (200 OK):**
```json
{
  "generated_at": "2025-12-22T10:30:00Z",
  "articles_count": 45,
  "timeframe": "H4",
  "asset": "XAU",
  "lang": "fa",
  "sources": [
    "Investing.com",
    "ForexFactory",
    "DailyFX",
    "FXStreet",
    "ForexLive"
  ],
  "summary": "**خلاصه بازار**\n\nطلا در معاملات امروز با افزایش تقاضا روبرو شده است...\n\n**تحلیل اقتصادی**\n\nداده‌های تورم آمریکا نشان می‌دهد...\n\n**تحلیل سیاسی**\n\nتنش‌های ژئوپلیتیکی در خاورمیانه...\n\n**وضعیت بازارهای مالی**\n\nشاخص دلار در حال کاهش است...\n\n**تیترهای مهم**\n\n1. افزایش قیمت طلا به بالاترین سطح 3 ماهه\n2. تصمیم فدرال رزرو درباره نرخ بهره\n3. تحولات بازار نفت\n\n**رویدادهای پیش رو**\n\n- فردا: اعلام داده‌های اشتغال آمریکا\n- این هفته: جلسه ECB\n\n**حال و هوای بازار**\n\nاحساسات کلی بازار مثبت و خریداران فعال هستند.",
  "success": true
}
```

**Processing Time:** 30-60 seconds (first time), 10-20 seconds (cached)

**Errors:**
- `500 Internal Server Error`: Scraping or analysis failed

---

### 7. Get Available Timeframes

**Endpoint:** `GET /api/timeframes/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Response (200 OK):**
```json
{
  "timeframes": {
    "M1": "1 Minute",
    "M5": "5 Minutes",
    "M15": "15 Minutes",
    "M30": "30 Minutes",
    "H1": "1 Hour",
    "H4": "4 Hours",
    "D1": "Daily",
    "W1": "Weekly",
    "MN1": "Monthly"
  },
  "trading_styles": {
    "scalp": {
      "name": "Scalping",
      "recommended_timeframes": ["M1", "M5", "M15"]
    },
    "day": {
      "name": "Day Trading",
      "recommended_timeframes": ["M15", "M30", "H1", "H4"]
    },
    "swing": {
      "name": "Swing Trading",
      "recommended_timeframes": ["H4", "D1", "W1"]
    },
    "position": {
      "name": "Position Trading",
      "recommended_timeframes": ["D1", "W1", "MN1"]
    }
  }
}
```

---

### 8. Multi-Timeframe Analysis

**Endpoint:** `GET /api/mtf/{pair}/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Query Parameters:**
- `timeframes` (optional): comma-separated (e.g., "H1,H4,D1")
- `trading_style` (optional): scalp, day, swing, position

**Example:** `GET /api/mtf/EURUSD/?timeframes=H1,H4,D1&trading_style=day`

**Response (200 OK):**
```json
{
  "pair": "EURUSD",
  "timeframes": ["H1", "H4", "D1"],
  "trading_style": "day",
  "analysis": {
    "note": "Multi-timeframe analysis pending - see TODO comments"
  },
  "generated_at": "2025-12-22T10:30:00Z"
}
```

**⚠️ Status:** ناقص - نیاز به پیاده‌سازی کامل با `llm/analyzer.py`

---

### 9. Translate Text

**Endpoint:** `POST /api/translate/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Request Body:**
```json
{
  "text": "Strong bullish momentum detected",
  "target_lang": "fa"
}
```

**Response (200 OK):**
```json
{
  "original": "Strong bullish momentum detected",
  "translated": "Strong bullish momentum detected",
  "target_lang": "fa"
}
```

**⚠️ Status:** ناقص - فعلاً placeholder است

---

### 10. Analyze Chart Image

**Endpoint:** `POST /api/analysis/chart-image/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Request Body:**
```json
{
  "pair": "EURUSD",
  "image_data": "base64-encoded-image-data",
  "timeframe": "H4",
  "trading_style": "day"
}
```

**Response (200 OK):**
```json
{
  "pair": "EURUSD",
  "timeframe": "H4",
  "analysis": {
    "trend": "Bullish",
    "patterns": ["Double Bottom", "Bullish Flag"],
    "key_levels": {
      "support": ["1.0850", "1.0820"],
      "resistance": ["1.0920", "1.0950"]
    },
    "recommendation": "BUY",
    "confidence": 78
  },
  "generated_at": "2025-12-22T10:30:00Z"
}
```

---

## 💼 Trading API

### 1. List Trading Accounts

**Endpoint:** `GET /api/trading-accounts/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "accounts": [
    {
      "id": 1,
      "broker": "MetaTrader5",
      "account_number": "12345678",
      "server": "Broker-Demo",
      "nickname": "My Demo Account",
      "balance": 10000.00,
      "equity": 10250.00,
      "risk_percent": 1.0,
      "is_active": true,
      "created_at": "2025-12-20T10:00:00Z"
    }
  ]
}
```

---

### 2. Add Trading Account

**Endpoint:** `POST /api/trading-accounts/add/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "broker": "MetaTrader5",
  "account_number": "12345678",
  "password": "account_password",
  "server": "Broker-Demo",
  "nickname": "My Demo Account",
  "risk_percent": 1.0
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "account": {
    "id": 1,
    "broker": "MetaTrader5",
    "account_number": "12345678",
    "server": "Broker-Demo",
    "nickname": "My Demo Account",
    "risk_percent": 1.0
  },
  "message": "Account added successfully"
}
```

**⚠️ Status:** ناقص - نیاز به:
- Encryption برای password
- اتصال واقعی به broker
- Validation

---

### 3. Refresh Trading Account

**Endpoint:** `POST /api/trading-accounts/{account_id}/refresh/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Account refresh pending - broker integration needed"
}
```

**⚠️ Status:** ناقص

---

### 4. Update Account Risk

**Endpoint:** `PATCH /api/trading-accounts/{account_id}/risk/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "risk_percent": 2.0
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Risk updated to 2.0%"
}
```

---

### 5. Delete Trading Account

**Endpoint:** `DELETE /api/trading-accounts/{account_id}/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Account deleted"
}
```

---

### 6. Get Available Robots

**Endpoint:** `GET /api/robots/available/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "robots": [
    {
      "id": "rsi_bot",
      "name": "RSI Trading Bot",
      "description": "Trades based on RSI indicator",
      "strategy": "Mean Reversion"
    },
    {
      "id": "breakout_bot",
      "name": "Breakout Bot",
      "description": "Trades breakouts of support/resistance",
      "strategy": "Breakout"
    }
  ]
}
```

**⚠️ Status:** ناقص - نیاز به ادغام با `/srv/strategy_bots/`

---

### 7. List User Robots

**Endpoint:** `GET /api/robots/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "robots": [
    {
      "id": 1,
      "name": "My RSI Bot",
      "robot_type": "rsi_bot",
      "pair": "EURUSD",
      "timeframe": "H1",
      "is_active": true,
      "created_at": "2025-12-20T10:00:00Z"
    }
  ]
}
```

---

### 8. Create Robot

**Endpoint:** `POST /api/robots/create/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "name": "My RSI Bot",
  "robot_type": "rsi_bot",
  "pair": "EURUSD",
  "timeframe": "H1",
  "config": {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "robot": {
    "id": 1,
    "name": "My RSI Bot",
    "robot_type": "rsi_bot",
    "pair": "EURUSD",
    "timeframe": "H1",
    "is_active": false
  }
}
```

**⚠️ Status:** ناقص

---

### 9. Update Robot

**Endpoint:** `PATCH /api/robots/{robot_id}/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "is_active": true,
  "config": {
    "rsi_period": 21
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Robot updated"
}
```

---

### 10. Delete Robot

**Endpoint:** `DELETE /api/robots/{robot_id}/delete/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Robot deleted"
}
```

---

## 📰 Scraping API

### 1. Trigger Scraping

**Endpoint:** `POST /api/scrape/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Request Body:** Empty or optional filters

**Response (200 OK):**
```json
{
  "message": "Scraping started in background",
  "note": "Full scraper integration pending - see TODO comments"
}
```

**⚠️ Status:** ناقص - نیاز به ادغام با `/srv/scrapers/`

---

### 2. Get News Articles

**Endpoint:** `GET /api/news/`  
**Authentication:** Not Required  
**Permission:** AllowAny

**Query Parameters:**
- `source` (optional): investing, forexfactory, dailyfx, fxstreet, forexlive
- `limit` (optional): default 50

**Response (200 OK):**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "EUR/USD rises on positive economic data",
      "source": "Investing.com",
      "url": "https://...",
      "published_at": "2025-12-22T09:00:00Z",
      "summary": "The euro gained against the dollar..."
    }
  ],
  "count": 45
}
```

---

### 3. Get Scrape Logs

**Endpoint:** `GET /api/scrape-logs/`  
**Authentication:** Required  
**Permission:** IsAuthenticated

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": 1,
      "source": "all",
      "articles_count": 45,
      "started_at": "2025-12-22T09:00:00Z",
      "completed_at": "2025-12-22T09:01:30Z",
      "is_successful": true
    }
  ]
}
```

---

## ❌ Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed explanation",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | OK | Request successful |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid input data |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | No permission |
| `404` | Not Found | Resource doesn't exist |
| `500` | Internal Server Error | Server error |

### Authentication Errors

```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "Invalid token."
}
```

---

## ⏱️ Rate Limiting

**⚠️ TODO:** Rate limiting هنوز پیاده‌سازی نشده

**پیشنهاد:**
- 100 requests/hour برای anonymous users
- 1000 requests/hour برای authenticated users
- 10000 requests/hour برای premium users

---

## 📝 نکات مهم

### 1. Trailing Slash
همه endpoints هم با `/` و هم بدون `/` کار می‌کنند:
- `/api/pairs/` ✅
- `/api/pairs` ✅

### 2. Content-Type
برای POST/PATCH requests:
```http
Content-Type: application/json
```

### 3. CORS
CORS برای development فعال است. در production باید محدود شود.

### 4. Pagination
**⚠️ TODO:** Pagination هنوز پیاده‌سازی نشده

---

## 🧪 نمونه Requests با cURL

### Sign Up
```bash
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'
```

### Sign In
```bash
curl -X POST http://localhost:8000/api/auth/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Get Analysis (با token)
```bash
curl -X GET http://localhost:8000/api/analysis/EURUSD/ \
  -H "Authorization: Token your-token-here"
```

### Daily Summary
```bash
curl -X GET "http://localhost:8000/api/summary/?asset=USD&lang=fa"
```

---

## 📚 نمونه Code

### JavaScript (Fetch API)

```javascript
// Sign In
async function signIn(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/signin/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data;
}

// Get Analysis
async function getAnalysis(pair) {
  const token = localStorage.getItem('token');
  const response = await fetch(`http://localhost:8000/api/analysis/${pair}/`, {
    headers: {
      'Authorization': `Token ${token}`,
    },
  });
  
  return await response.json();
}
```

### Python (requests)

```python
import requests

# Sign In
response = requests.post(
    'http://localhost:8000/api/auth/signin/',
    json={
        'email': 'test@example.com',
        'password': 'testpass123'
    }
)
token = response.json()['token']

# Get Analysis
response = requests.get(
    'http://localhost:8000/api/analysis/EURUSD/',
    headers={'Authorization': f'Token {token}'}
)
analysis = response.json()
```

---

## 🔄 WebSocket (Future)

**⚠️ TODO:** WebSocket برای real-time updates هنوز پیاده‌سازی نشده

**پیشنهاد:**
```
ws://localhost:8000/ws/prices/{pair}/
ws://localhost:8000/ws/signals/
ws://localhost:8000/ws/robots/{robot_id}/
```

---

**یادداشت:** این مستندات با توسعه API به‌روز می‌شود.
