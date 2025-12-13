"""
FastAPI Web Application for Forex Analysis Assistant
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config.settings import DATA_DIR, DEFAULT_PAIRS, PAIR_CONFIGS
from config.timeframes import TIMEFRAME_NAMES, TRADING_STYLES, Timeframe
from scrapers import ScraperManager
from scrapers.base_scraper import NewsArticle
from llm.analyzer import ForexAnalyzer, MarketAnalysis, TradeRecommendation, MultiTimeframeAnalysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Forex Analysis Assistant",
    description="AI-powered forex market analysis and trade recommendations",
    version="1.0.0"
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Static files (for locales and other assets)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize components
scraper_manager = ScraperManager(DATA_DIR)
analyzer = ForexAnalyzer()

# Pairs configuration file
PAIRS_FILE = DATA_DIR / "pairs.json"


# Request/Response Models
class PairConfig(BaseModel):
    volatility: str = "medium"
    default_sl_pips: int = 30
    default_tp_pips: int = 60
    keywords: List[str] = []


class AddPairRequest(BaseModel):
    pair: str
    config: Optional[PairConfig] = None


class AnalysisResponse(BaseModel):
    pair: str
    analysis: dict
    recommendation: dict
    generated_at: str


# Helper functions
def load_pairs() -> dict:
    """Load pairs configuration"""
    if PAIRS_FILE.exists():
        with open(PAIRS_FILE, "r") as f:
            return json.load(f)
    return {pair: PAIR_CONFIGS.get(pair, {}) for pair in DEFAULT_PAIRS}


def save_pairs(pairs: dict):
    """Save pairs configuration"""
    with open(PAIRS_FILE, "w") as f:
        json.dump(pairs, f, indent=2)


# Background task for scraping
async def background_scrape():
    """Background task to scrape news"""
    pairs = list(load_pairs().keys())
    await scraper_manager.scrape_all(pairs)


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with dashboard"""
    pairs = load_pairs()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "pairs": list(pairs.keys()),
        "title": "Forex Analysis Assistant"
    })


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Sign up page"""
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """Sign in page"""
    return templates.TemplateResponse("signin.html", {"request": request})


@app.get("/chart", response_class=HTMLResponse)
async def chart_view(request: Request):
    """Chart view page for viewing charts in new tab"""
    return templates.TemplateResponse("chart_view.html", {"request": request})


@app.get("/api/pairs")
async def list_pairs():
    """List all configured currency pairs"""
    return {"pairs": load_pairs()}


@app.post("/api/pairs")
async def add_pair(request: AddPairRequest):
    """Add a new currency pair"""
    pairs = load_pairs()
    
    pair = request.pair.upper().replace("/", "")
    if len(pair) != 6:
        raise HTTPException(status_code=400, detail="Invalid pair format. Use format like EURUSD")
    
    if pair in pairs:
        raise HTTPException(status_code=400, detail=f"Pair {pair} already exists")
    
    config = request.config.model_dump() if request.config else {
        "volatility": "medium",
        "default_sl_pips": 30,
        "default_tp_pips": 60,
        "keywords": [pair[:3], pair[3:]]
    }
    
    pairs[pair] = config
    save_pairs(pairs)
    
    # Update PAIR_CONFIGS
    PAIR_CONFIGS[pair] = config
    
    return {"message": f"Pair {pair} added successfully", "pair": pair, "config": config}


@app.delete("/api/pairs/{pair}")
async def remove_pair(pair: str):
    """Remove a currency pair"""
    pairs = load_pairs()
    pair = pair.upper()
    
    if pair not in pairs:
        raise HTTPException(status_code=404, detail=f"Pair {pair} not found")
    
    del pairs[pair]
    save_pairs(pairs)
    
    return {"message": f"Pair {pair} removed successfully"}


@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger news scraping"""
    background_tasks.add_task(background_scrape)
    return {"message": "Scraping started in background"}


@app.get("/api/news")
async def get_news(pair: Optional[str] = None, limit: int = 50):
    """Get scraped news articles"""
    articles = await scraper_manager.load_articles()
    
    if pair:
        pair = pair.upper()
        articles = scraper_manager.filter_by_pair(articles, pair)
    
    return {
        "count": len(articles[:limit]),
        "articles": [a.model_dump() for a in articles[:limit]]
    }


@app.get("/api/analysis/{pair}")
async def get_analysis(pair: str, timeframe: str = "H1", trading_style: str = "day"):
    """Get AI analysis for a currency pair with specific timeframe and trading style"""
    pair = pair.upper()
    pairs = load_pairs()
    
    if pair not in pairs:
        raise HTTPException(status_code=404, detail=f"Pair {pair} not configured")
    
    # Load articles
    articles = await scraper_manager.load_articles()
    
    if not articles:
        # Try to scrape first
        articles = await scraper_manager.scrape_all(list(pairs.keys()))
    
    # Generate analysis with timeframe and trading style context
    analysis = await analyzer.analyze_pair(pair, articles, timeframe=timeframe, trading_style=trading_style)
    recommendation = await analyzer.get_trade_recommendation(pair, analysis, timeframe=timeframe, trading_style=trading_style)
    
    return AnalysisResponse(
        pair=pair,
        analysis=analysis.model_dump(),
        recommendation=recommendation.model_dump(),
        generated_at=datetime.now().isoformat()
    )


@app.get("/api/analysis")
async def get_all_analysis(
    timeframe: str = "H1",
    trading_style: str = "day"
):
    """Get analysis for all configured pairs with timeframe and trading style"""
    pairs = load_pairs()
    articles = await scraper_manager.load_articles()
    
    if not articles:
        articles = await scraper_manager.scrape_all(list(pairs.keys()))
    
    # Get style timeframes
    style_config = analyzer.TRADING_STYLES.get(trading_style, analyzer.TRADING_STYLES['day'])
    timeframes = style_config.get('timeframes', [timeframe])
    
    results = []
    for pair in pairs.keys():
        analysis = await analyzer.analyze_pair(pair, articles, timeframe=timeframe, trading_style=trading_style)
        recommendation = await analyzer.get_trade_recommendation(
            pair, analysis, 
            timeframe=timeframe, 
            trading_style=trading_style,
            timeframes=timeframes
        )
        results.append({
            "pair": pair,
            "analysis": analysis.model_dump(),
            "recommendation": recommendation.model_dump(),
            "timeframe": timeframe,
            "trading_style": trading_style
        })
    
    return {
        "generated_at": datetime.now().isoformat(),
        "pairs_count": len(results),
        "timeframe": timeframe,
        "trading_style": trading_style,
        "results": results
    }


@app.get("/api/summary")
async def get_daily_summary(timeframe: str = "H1", asset: str = "USD", lang: str = "fa"):
    """Get daily market summary with asset trend analysis"""
    articles = await scraper_manager.load_articles()
    
    if not articles:
        pairs = load_pairs()
        articles = await scraper_manager.scrape_all(list(pairs.keys()))
    
    summary = await analyzer.generate_daily_summary(articles, timeframe=timeframe, asset=asset, lang=lang)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "articles_count": len(articles),
        "timeframe": timeframe,
        "asset": asset,
        "lang": lang,
        "summary": summary
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pairs_configured": len(load_pairs())
    }


# ============== Translation API Endpoint ==============

class TranslateRequest(BaseModel):
    text: str
    target_lang: str


@app.post("/api/translate")
async def translate_text(request: TranslateRequest):
    """Translate text to target language using AI"""
    translated = await analyzer.translate_text(request.text, request.target_lang)
    return {
        "original": request.text,
        "translated": translated,
        "target_lang": request.target_lang
    }


# ============== Multi-Timeframe API Endpoints ==============

@app.get("/api/timeframes")
async def get_timeframes():
    """Get available timeframes and trading styles"""
    return {
        "timeframes": TIMEFRAME_NAMES,
        "trading_styles": TRADING_STYLES
    }


@app.get("/api/mtf/{pair}")
async def get_mtf_analysis(
    pair: str,
    timeframes: str = "H1",
    trading_style: str = "day"
):
    """
    Get Multi-Timeframe Analysis for a currency pair
    
    - **pair**: Currency pair (e.g., EURUSD)
    - **timeframes**: Comma-separated list of timeframes (e.g., M1,M5,M15)
    - **trading_style**: scalp, day, swing, position
    """
    pair = pair.upper()
    pairs = load_pairs()
    
    if pair not in pairs:
        raise HTTPException(status_code=404, detail=f"Pair {pair} not configured")
    
    # Parse timeframes
    tf_list = [tf.strip() for tf in timeframes.split(',')]
    primary_tf = tf_list[0] if tf_list else "H1"
    
    # Map short style names to full names
    style_map = {
        'scalp': 'scalping',
        'day': 'day_trading',
        'swing': 'swing_trading',
        'position': 'position_trading'
    }
    full_style = style_map.get(trading_style, trading_style)
    
    # Validate trading style
    if full_style not in TRADING_STYLES:
        full_style = 'day_trading'
    
    # Load articles
    articles = await scraper_manager.load_articles()
    if not articles:
        articles = await scraper_manager.scrape_all(list(pairs.keys()))
    
    # Perform MTF analysis
    mtf_analysis = await analyzer.analyze_multi_timeframe(
        pair=pair,
        primary_tf=primary_tf,
        articles=articles,
        trading_style=full_style,
        timeframes=tf_list
    )
    
    return {
        "pair": pair,
        "timeframes": tf_list,
        "trading_style": trading_style,
        "analysis": mtf_analysis.model_dump(),
        "generated_at": datetime.now().isoformat()
    }


@app.get("/api/analysis/{pair}/{timeframe}")
async def get_timeframe_analysis(
    pair: str,
    timeframe: str,
    trading_style: str = "day_trading",
    risk_profile: str = "moderate"
):
    """
    Get analysis for a specific timeframe
    
    - **pair**: Currency pair
    - **timeframe**: Specific timeframe (M15, H1, H4, etc.)
    - **trading_style**: Trading style
    - **risk_profile**: conservative, moderate, aggressive
    """
    pair = pair.upper()
    pairs = load_pairs()
    
    if pair not in pairs:
        raise HTTPException(status_code=404, detail=f"Pair {pair} not configured")
    
    articles = await scraper_manager.load_articles()
    if not articles:
        articles = await scraper_manager.scrape_all(list(pairs.keys()))
    
    result = await analyzer.analyze_specific_timeframe(
        pair=pair,
        timeframe=timeframe,
        articles=articles,
        trading_style=trading_style,
        risk_profile=risk_profile
    )
    
    return {
        "pair": pair,
        "timeframe": timeframe,
        "analysis": result,
        "generated_at": datetime.now().isoformat()
    }


# ============== Authentication System ==============
import hashlib
import secrets

USERS_FILE = DATA_DIR / "users.json"

# Import session cache for persistent sessions
try:
    from web.services.session_cache import get_session_cache
except ImportError:
    try:
        from services.session_cache import get_session_cache
    except ImportError:
        get_session_cache = None

# Initialize session cache
session_cache = get_session_cache() if get_session_cache else None


def load_users() -> dict:
    """Load users from file"""
    if USERS_FILE.exists():
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """Save users to file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """Generate a random token"""
    return secrets.token_hex(32)


def get_user_email_from_token(token: str) -> str:
    """Get user email from token, checking cache first then users file"""
    # First check session cache (survives server restarts)
    if session_cache:
        cached_user = session_cache.get_user_by_token(token)
        if cached_user:
            return cached_user.get("email")
    
    # Fallback to users file
    users = load_users()
    for email, user in users.items():
        if user.get("token") == token:
            return email
    
    return None


class SignInRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


@app.post("/api/auth/signin")
async def sign_in(request: SignInRequest):
    """Sign in user"""
    users = load_users()
    
    email = request.email.lower().strip()
    password_hash = hash_password(request.password)
    
    if email not in users:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = users[email]
    if user.get("password") != password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate token
    token = generate_token()
    
    # Update last login
    user["last_login"] = datetime.now().isoformat()
    user["token"] = token
    users[email] = user
    save_users(users)
    
    # Store session in cache for persistence across restarts
    if session_cache:
        session_cache.create_session(
            token=token,
            user_email=email,
            user_data={
                "name": user.get("name", email.split("@")[0]),
                "created_at": user.get("created_at")
            }
        )
    
    return {
        "user": {
            "email": email,
            "name": user.get("name", email.split("@")[0]),
            "created_at": user.get("created_at")
        },
        "token": token
    }


@app.post("/api/auth/signup")
async def sign_up(request: SignUpRequest):
    """Sign up new user"""
    users = load_users()
    
    email = request.email.lower().strip()
    
    # Validate email format
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check if user exists
    if email in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Create user
    token = generate_token()
    users[email] = {
        "name": request.name.strip(),
        "password": hash_password(request.password),
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
        "token": token
    }
    save_users(users)
    
    logger.info(f"New user registered: {email}")
    
    # Store session in cache for persistence across restarts
    if session_cache:
        session_cache.create_session(
            token=token,
            user_email=email,
            user_data={
                "name": request.name.strip(),
                "created_at": users[email]["created_at"]
            }
        )
    
    return {
        "user": {
            "email": email,
            "name": request.name.strip(),
            "created_at": users[email]["created_at"]
        },
        "token": token
    }


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and invalidate session"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and session_cache:
        token = auth_header[7:]
        session_cache.invalidate_session(token)
    return {"message": "Logged out successfully"}


@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """Get current user info"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    
    # First check session cache (survives server restarts)
    if session_cache:
        cached_user = session_cache.get_user_by_token(token)
        if cached_user:
            return cached_user
    
    # Fallback to users file
    users = load_users()
    
    for email, user in users.items():
        if user.get("token") == token:
            return {
                "email": email,
                "name": user.get("name", email.split("@")[0]),
                "created_at": user.get("created_at")
            }
    
    raise HTTPException(status_code=401, detail="Invalid token")


# ============== Trading Accounts API ==============
try:
    from web.services.trading_accounts import trading_accounts_service, BrokerType
except ImportError:
    try:
        from services.trading_accounts import trading_accounts_service, BrokerType
    except ImportError:
        # Fallback - trading accounts service not available
        trading_accounts_service = None
        BrokerType = None
        logger.warning("Trading accounts service not available")


class AddTradingAccountRequest(BaseModel):
    broker: str
    login: str
    password: str
    server: str
    risk_percent: float = 2.0
    nickname: str = ""


class UpdateRiskRequest(BaseModel):
    risk_percent: float


@app.post("/api/trading-accounts")
async def add_trading_account(request: Request, data: AddTradingAccountRequest):
    """Add a new trading account and connect to broker"""
    if not trading_accounts_service:
        raise HTTPException(status_code=503, detail="Trading accounts service not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await trading_accounts_service.add_account(
        user_id=user_email,
        broker=data.broker,
        login=data.login,
        password=data.password,
        server=data.server,
        risk_percent=data.risk_percent,
        nickname=data.nickname
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to add account"))
    
    return result


@app.get("/api/trading-accounts")
async def get_trading_accounts(request: Request):
    """Get all trading accounts for the current user"""
    if not trading_accounts_service:
        return {"accounts": []}
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    accounts = await trading_accounts_service.get_user_accounts(user_email)
    return {"accounts": accounts}


@app.post("/api/trading-accounts/{account_id}/refresh")
async def refresh_trading_account(account_id: str, request: Request):
    """Refresh account information by reconnecting to broker"""
    if not trading_accounts_service:
        raise HTTPException(status_code=503, detail="Trading accounts service not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await trading_accounts_service.refresh_account(user_email, account_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to refresh account"))
    
    return result


@app.delete("/api/trading-accounts/{account_id}")
async def delete_trading_account(account_id: str, request: Request):
    """Delete a trading account"""
    if not trading_accounts_service:
        raise HTTPException(status_code=503, detail="Trading accounts service not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await trading_accounts_service.delete_account(user_email, account_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete account"))
    
    return result


@app.patch("/api/trading-accounts/{account_id}/risk")
async def update_account_risk(account_id: str, request: Request, data: UpdateRiskRequest):
    """Update risk percentage for an account"""
    if not trading_accounts_service:
        raise HTTPException(status_code=503, detail="Trading accounts service not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    users = load_users()
    
    user_email = None
    for email, user in users.items():
        if user.get("token") == token:
            user_email = email
            break
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await trading_accounts_service.update_risk(user_email, account_id, data.risk_percent)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update risk"))
    
    return result


# ============== Trading Robots API ==============
# Try unified system first, then fallback to individual modules
try:
    from trading.unified_robots import (
        UnifiedRobotManager, UnifiedRobotRegistry,
        UnifiedSLFactory, UnifiedTPFactory,
        create_unified_manager
    )
    UNIFIED_ROBOTS_AVAILABLE = True
except ImportError:
    UNIFIED_ROBOTS_AVAILABLE = False

try:
    from trading import (
        RobotManager, UserSubscription, create_robot_manager,
        RobotRegistry, Timeframe, SLStrategy, TPStrategy
    )
    ROBOTS_AVAILABLE = True
except ImportError:
    ROBOTS_AVAILABLE = False

if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
    logger.warning("Trading robots modules not available")

# Store robot managers per user
_robot_managers: dict = {}
_unified_managers: dict = {}


def get_robot_manager(user_email: str, subscription_plan: str = "free"):
    """Get or create robot manager for user"""
    is_premium = subscription_plan == "premium"
    
    # Prefer unified manager
    if UNIFIED_ROBOTS_AVAILABLE:
        if user_email not in _unified_managers:
            _unified_managers[user_email] = create_unified_manager(user_email, is_premium)
        return _unified_managers[user_email]
    
    # Fallback to old manager
    if ROBOTS_AVAILABLE:
        if user_email not in _robot_managers:
            _robot_managers[user_email] = create_robot_manager(user_email, subscription_plan)
        return _robot_managers[user_email]
    
    return None


class CreateRobotRequest(BaseModel):
    robot_name: str
    symbol: str = "EURUSD"
    timeframe: str = "1h"
    sl_strategy: str = "atr"
    tp_strategy: str = "risk_reward"
    sl_params: dict = {}
    tp_params: dict = {}
    risk_percent: float = 1.0


class UpdateRobotRequest(BaseModel):
    sl_strategy: Optional[str] = None
    tp_strategy: Optional[str] = None
    sl_params: Optional[dict] = None
    tp_params: Optional[dict] = None
    risk_percent: Optional[float] = None


@app.get("/api/robots/available")
async def get_available_robots(request: Request):
    """Get available robots and strategies for the user"""
    if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
        return {"robots": [], "sl_strategies": [], "tp_strategies": [], "timeframes": []}
    
    auth_header = request.headers.get("Authorization", "")
    subscription_plan = "free"
    is_premium = False
    
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user_email = get_user_email_from_token(token)
        if user_email:
            # TODO: Get actual subscription from database
            subscription_plan = "free"
            is_premium = subscription_plan == "premium"
    
    # Use unified system if available
    if UNIFIED_ROBOTS_AVAILABLE:
        return {
            "robots": UnifiedRobotRegistry.get_all(),
            "sl_strategies": UnifiedSLFactory.get_available(is_premium),
            "tp_strategies": UnifiedTPFactory.get_available(is_premium),
            "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"],
            "subscription": subscription_plan
        }
    
    # Fallback to old system
    subscription = UserSubscription(subscription_plan)
    
    return {
        "robots": [
            {
                "name": r["name"],
                "description": r["description"],
                "available": subscription.can_use_robot(r["name"])
            }
            for r in RobotRegistry.list_all()
        ],
        "sl_strategies": subscription.get_available_sl_strategies(),
        "tp_strategies": subscription.get_available_tp_strategies(),
        "timeframes": [tf.value for tf in Timeframe],
        "subscription": subscription_plan
    }


@app.post("/api/robots")
async def create_robot(request: Request, data: CreateRobotRequest):
    """Create a new trading robot"""
    if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Trading robots not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    manager = get_robot_manager(user_email)
    if not manager:
        raise HTTPException(status_code=503, detail="Robot manager not available")
    
    result = manager.create_robot(
        robot_name=data.robot_name,
        symbol=data.symbol,
        timeframe=data.timeframe,
        sl_strategy=data.sl_strategy,
        tp_strategy=data.tp_strategy,
        sl_params=data.sl_params or {},
        tp_params=data.tp_params or {},
        risk_percent=data.risk_percent
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create robot"))
    
    return result


@app.get("/api/robots")
async def get_user_robots(request: Request):
    """Get user's active robots"""
    if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
        return {"robots": []}
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    manager = get_robot_manager(user_email)
    if not manager:
        return {"robots": []}
    
    return {
        "robots": manager.get_active_robots(),
        "options": manager.get_available_options()
    }


@app.patch("/api/robots/{robot_id}")
async def update_robot(robot_id: str, request: Request, data: UpdateRobotRequest):
    """Update robot configuration"""
    if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Trading robots not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    manager = get_robot_manager(user_email)
    if not manager:
        raise HTTPException(status_code=503, detail="Robot manager not available")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = manager.update_robot_config(robot_id, **update_data)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update robot"))
    
    return result


@app.delete("/api/robots/{robot_id}")
async def delete_robot(robot_id: str, request: Request):
    """Delete a robot"""
    if not UNIFIED_ROBOTS_AVAILABLE and not ROBOTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Trading robots not available")
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    user_email = get_user_email_from_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    manager = get_robot_manager(user_email)
    if not manager:
        raise HTTPException(status_code=503, detail="Robot manager not available")
    
    result = manager.delete_robot(robot_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete robot"))
    
    return result


def create_app():
    """Factory function to create the app"""
    return app
