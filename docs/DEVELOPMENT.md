# 💻 راهنمای توسعه‌دهنده

**نسخه:** 2.0  
**تاریخ:** 2025-12-22

---

## 📋 فهرست مطالب

1. [محیط توسعه](#محیط-توسعه)
2. [ساختار پروژه](#ساختار-پروژه)
3. [استانداردهای کدنویسی](#استانداردهای-کدنویسی)
4. [Git Workflow](#git-workflow)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [بهترین روش‌ها](#بهترین-روش‌ها)
8. [مشارکت در پروژه](#مشارکت-در-پروژه)

---

## 🛠️ محیط توسعه

### نصب محیط Development

```bash
# Clone repository
git clone https://github.com/yourusername/forex-analysis-assistant.git
cd forex-analysis-assistant

# ایجاد virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows

# نصب dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # اگر وجود دارد

# نصب pre-commit hooks
pre-commit install  # اگر استفاده می‌کنید
```

### IDE Setup

#### VS Code (پیشنهادی)

**Extensions:**
- Python
- Pylance
- Django
- Docker
- GitLens
- REST Client

**settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "[python]": {
    "editor.rulers": [88, 120]
  }
}
```

#### PyCharm

1. Open Project
2. Configure Python Interpreter → venv
3. Enable Django Support
4. Configure Database connection

---

## 📁 ساختار پروژه

### ساختار کلی

```
/srv/
├── 📂 apps/                    # Django Applications
│   ├── accounts/               # احراز هویت و کاربران
│   ├── analysis/               # تحلیل بازار
│   ├── trading/                # معاملات
│   └── scraping/               # جمع‌آوری اخبار
│
├── 📂 forex_assistant/         # Django Project
│   ├── settings.py             # تنظیمات اصلی
│   ├── urls.py                 # URL routing
│   ├── celery.py               # Celery config
│   └── wsgi.py / asgi.py
│
├── 📂 scrapers/                # ماژول اسکرپینگ (مستقل)
│   ├── base_scraper.py
│   ├── scraper_manager.py
│   └── [5 scrapers].py
│
├── 📂 llm/                     # AI/LLM ماژول‌ها (مستقل)
│   ├── analyzer.py             # تحلیلگر اصلی
│   ├── chart_analyzer.py
│   └── prompts.py
│
├── 📂 trading/                 # ماژول‌های معاملاتی (مستقل)
│   ├── robot_manager.py
│   ├── unified_robots.py
│   └── ...
│
├── 📂 strategy_bots/           # ربات‌های استراتژیک (مستقل)
│   ├── base_bot.py
│   ├── rsi_bot.py
│   └── ...
│
├── 📂 web/                     # FastAPI App (Legacy)
│   ├── app.py
│   ├── services/
│   └── templates/
│
├── 📂 templates/               # Django Templates
│   └── emails/
│
├── 📂 deploy/                  # Docker & Deployment
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── ...
│
├── 📂 docs/                    # مستندات (پیشنهادی)
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── ...
│
├── manage.py                   # Django CLI
├── main.py                     # FastAPI entry (Legacy)
└── requirements.txt
```

### ساختار یک Django App

```
apps/example_app/
├── __init__.py
├── admin.py                    # Django Admin config
├── apps.py                     # App config
├── models.py                   # Database models
├── serializers.py              # DRF Serializers
├── views.py                    # API Views
├── urls.py                     # URL routing
├── tasks.py                    # Celery tasks
├── services.py                 # Business logic
├── utils.py                    # Helper functions
├── migrations/                 # Database migrations
│   ├── __init__.py
│   └── 0001_initial.py
└── tests/                      # Tests
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

---

## 📝 استانداردهای کدنویسی

### Python Style Guide

**پیروی از PEP 8** با تنظیمات زیر:

```python
# Line length
max-line-length = 88  # Black default

# Imports
# 1. Standard library
# 2. Third-party
# 3. Local/Django apps

import os
import sys
from datetime import datetime

from django.db import models
from rest_framework import serializers

from apps.accounts.models import User
```

### Naming Conventions

```python
# Variables & Functions: snake_case
user_email = "test@example.com"
def get_user_by_email(email):
    pass

# Classes: PascalCase
class UserSerializer(serializers.ModelSerializer):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Docstrings

```python
def analyze_pair(pair: str, timeframe: str = 'H1') -> dict:
    """
    تحلیل یک جفت ارز با استفاده از AI
    
    Args:
        pair (str): نماد جفت ارز (e.g., 'EURUSD')
        timeframe (str): بازه زمانی (default: 'H1')
    
    Returns:
        dict: نتیجه تحلیل شامل sentiment و recommendation
    
    Raises:
        ValueError: اگر pair معتبر نباشد
        APIError: اگر OpenAI API خطا دهد
    
    Example:
        >>> result = analyze_pair('EURUSD', 'H4')
        >>> print(result['sentiment'])
        'Bullish'
    """
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional, Union

def get_analysis(
    pair: str,
    timeframe: str = 'H1',
    include_chart: bool = False
) -> Dict[str, any]:
    """Get market analysis"""
    pass

def scrape_news(
    sources: List[str],
    pairs: Optional[List[str]] = None
) -> List[NewsArticle]:
    """Scrape news from sources"""
    pass
```

---

## 🔀 Git Workflow

### Branch Strategy

```
main (production)
  ↓
develop (staging)
  ↓
feature/feature-name
fix/bug-name
hotfix/critical-fix
```

### Commit Messages

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: ویژگی جدید
- `fix`: رفع باگ
- `docs`: تغییرات مستندات
- `style`: فرمت کد (بدون تغییر منطق)
- `refactor`: بازنویسی کد
- `test`: اضافه کردن تست
- `chore`: کارهای نگهداری

**Examples:**
```bash
feat(analysis): add multi-timeframe analysis support

- Implement capture_multi_timeframe_charts()
- Add analyze_multi_timeframe_charts() in chart_analyzer
- Update auto_chart_analysis() with MTF parameters

Closes #123
```

```bash
fix(email): resolve SMTP authentication error

The email service was failing due to incorrect password format.
Fixed by removing spaces from app password.

Fixes #456
```

### Workflow

```bash
# 1. ایجاد branch جدید
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature

# 2. کار روی feature
# ... make changes ...
git add .
git commit -m "feat(scope): description"

# 3. Push و PR
git push origin feature/my-new-feature
# Create Pull Request on GitHub

# 4. بعد از merge
git checkout develop
git pull origin develop
git branch -d feature/my-new-feature
```

---

## 🧪 Testing

### نوشتن تست‌ها

#### Unit Tests

```python
# apps/accounts/tests/test_models.py
from django.test import TestCase
from apps.accounts.models import User

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
    
    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'test@example.com')
```

#### API Tests

```python
# apps/accounts/tests/test_views.py
from rest_framework.test import APITestCase
from rest_framework import status

class AuthAPITest(APITestCase):
    def test_signup(self):
        """Test user signup"""
        data = {
            'email': 'new@example.com',
            'password': 'newpass123',
            'name': 'New User'
        }
        response = self.client.post('/api/auth/signup/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'new@example.com')
    
    def test_signin(self):
        """Test user signin"""
        # Create user first
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        response = self.client.post('/api/auth/signin/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
```

### اجرای تست‌ها

```bash
# همه تست‌ها
python manage.py test

# یک app خاص
python manage.py test apps.accounts

# یک فایل خاص
python manage.py test apps.accounts.tests.test_models

# با coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # HTML report در htmlcov/
```

### Test Coverage

**هدف:** حداقل 80% coverage

```bash
# نصب coverage
pip install coverage

# اجرا با coverage
coverage run --source='apps' manage.py test
coverage report

# نمایش خطوط بدون تست
coverage report -m

# HTML report
coverage html
open htmlcov/index.html
```

---

## 🐛 Debugging

### Django Debug Toolbar

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
```

### Django Shell

```bash
# Django shell
python manage.py shell

# IPython shell (بهتر)
pip install ipython
python manage.py shell

# Django shell_plus (django-extensions)
pip install django-extensions
python manage.py shell_plus
```

**مثال:**
```python
from apps.accounts.models import User
from apps.analysis.models import CurrencyPair

# Query users
users = User.objects.all()
user = User.objects.get(email='test@example.com')

# Test email service
from apps.accounts.email_service import get_email_service
email_service = get_email_service()
verification = email_service.send_verification_email(user, 'fa')
print(f"Code: {verification.code}")
```

### Database Queries

```python
# نمایش SQL queries
from django.db import connection
print(connection.queries)

# یا با django-debug-toolbar
# در browser: Debug Toolbar → SQL panel

# Explain query
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("EXPLAIN SELECT * FROM accounts_user")
    print(cursor.fetchall())
```

### Docker Debugging

```bash
# Logs
docker compose logs -f web
docker compose logs -f celery_worker

# Shell در container
docker compose exec web bash
docker compose exec web python manage.py shell

# Database shell
docker compose exec db psql -U forex_user -d forex_assistant

# Redis CLI
docker compose exec redis redis-cli
```

---

## ✅ بهترین روش‌ها

### 1. Models

```python
# خوب ✅
class User(AbstractBaseUser):
    email = models.EmailField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.email

# بد ❌
class User(AbstractBaseUser):
    email = models.EmailField()  # بدون unique و index
    # بدون __str__
    # بدون Meta
```

### 2. Views

```python
# خوب ✅
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_analysis(request):
    """Create new analysis"""
    serializer = AnalysisSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    analysis = serializer.save(user=request.user)
    return Response(
        AnalysisSerializer(analysis).data,
        status=status.HTTP_201_CREATED
    )

# بد ❌
def create_analysis(request):
    # بدون decorator
    # بدون validation
    # بدون error handling
    analysis = Analysis.objects.create(**request.data)
    return Response(analysis)
```

### 3. Services Layer

```python
# خوب ✅
# apps/analysis/services.py
class AnalysisService:
    """Business logic for analysis"""
    
    def __init__(self):
        self.analyzer = ForexAnalyzer()
    
    async def generate_analysis(
        self,
        pair: str,
        timeframe: str = 'H1'
    ) -> MarketAnalysis:
        """Generate analysis for pair"""
        # Business logic here
        pass

# views.py
@api_view(['GET'])
def get_analysis(request, pair):
    service = AnalysisService()
    analysis = await service.generate_analysis(pair)
    return Response(AnalysisSerializer(analysis).data)

# بد ❌
# همه منطق در view
@api_view(['GET'])
def get_analysis(request, pair):
    # 100 خط منطق کسب‌وکار در view
    pass
```

### 4. Query Optimization

```python
# خوب ✅
# استفاده از select_related برای ForeignKey
users = User.objects.select_related('subscription').all()

# استفاده از prefetch_related برای ManyToMany
analyses = MarketAnalysis.objects.prefetch_related('indicators').all()

# فقط فیلدهای مورد نیاز
users = User.objects.only('email', 'name').all()

# بد ❌
# N+1 query problem
users = User.objects.all()
for user in users:
    print(user.subscription.plan)  # هر بار یک query!
```

### 5. Error Handling

```python
# خوب ✅
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    logger.warning(f"User not found: {email}")
    return Response(
        {'error': 'User not found'},
        status=status.HTTP_404_NOT_FOUND
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return Response(
        {'error': 'Internal server error'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# بد ❌
user = User.objects.get(email=email)  # ممکن است crash کند
```

### 6. Async/Await

```python
# خوب ✅
async def scrape_news():
    """Async scraping"""
    async with aiohttp.ClientSession() as session:
        tasks = [scraper.scrape(session) for scraper in scrapers]
        results = await asyncio.gather(*tasks)
    return results

# بد ❌
def scrape_news():
    """Sync scraping - کند!"""
    results = []
    for scraper in scrapers:
        results.append(scraper.scrape())  # یکی یکی
    return results
```

---

## 🤝 مشارکت در پروژه

### قبل از شروع

1. **Issue بسازید** یا یک issue موجود را assign کنید
2. **Branch جدید** از develop بسازید
3. **تست بنویسید** برای کد جدید
4. **مستندات** را به‌روز کنید

### Pull Request Checklist

- [ ] کد از PEP 8 پیروی می‌کند
- [ ] تست‌ها نوشته شده و pass می‌شوند
- [ ] مستندات به‌روز شده
- [ ] Commit messages استاندارد هستند
- [ ] هیچ conflict وجود ندارد
- [ ] Code review انجام شده

### Code Review

**به عنوان نویسنده:**
- کد را خودتان review کنید قبل از PR
- توضیحات کامل در PR description
- پاسخ به comments سریع و محترمانه

**به عنوان reviewer:**
- بررسی منطق کد، نه فقط syntax
- پیشنهادات سازنده
- تست کردن تغییرات

---

## 📚 منابع مفید

### Django
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)

### Python
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Async/Await](https://docs.python.org/3/library/asyncio.html)

### Testing
- [Django Testing](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [pytest-django](https://pytest-django.readthedocs.io/)

### Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [Flake8 Linter](https://flake8.pycqa.org/)
- [mypy Type Checker](http://mypy-lang.org/)

---

## 🎯 نکات پایانی

### DRY (Don't Repeat Yourself)
اگر کدی را بیش از 2 بار نوشتید، آن را به تابع/کلاس تبدیل کنید.

### KISS (Keep It Simple, Stupid)
ساده‌ترین راه‌حل معمولاً بهترین است.

### YAGNI (You Aren't Gonna Need It)
فقط چیزی بنویسید که الان نیاز دارید، نه چیزی که شاید آینده نیاز باشد.

### SOLID Principles
- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

---

**موفق باشید! 🚀**
