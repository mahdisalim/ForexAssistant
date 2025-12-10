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


def create_app():
    """Factory function to create the app"""
    return app
