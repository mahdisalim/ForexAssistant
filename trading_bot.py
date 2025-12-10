"""
Automated Trading Bot
Phase 3: Algorithmic Trading with AI Analysis

This bot:
1. Scrapes news from multiple sources
2. Analyzes market with AI
3. Generates trade recommendations
4. Executes trades via MetaTrader 5
5. Manages risk and positions
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import DATA_DIR, PAIR_CONFIGS
from scrapers import ScraperManager
from llm.analyzer import ForexAnalyzer, TradeRecommendation
from indicators.risk_manager import RiskManager
from indicators.trade_executor import TradeExecutor, OrderType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBot:
    """
    AI-powered forex trading bot
    
    Combines news analysis with automated trade execution
    """
    
    # High-impact news events to avoid trading
    HIGH_IMPACT_EVENTS = [
        "NFP", "Non-Farm Payroll",
        "CPI", "Consumer Price Index",
        "FOMC", "Federal Reserve",
        "ECB", "Interest Rate Decision",
        "GDP", "Gross Domestic Product"
    ]
    
    def __init__(
        self,
        mt5_login: int = 0,
        mt5_password: str = "",
        mt5_server: str = "",
        account_balance: float = 10000.0,
        risk_percent: float = 1.0,
        min_confidence: int = 60,
        demo_mode: bool = True
    ):
        self.scraper_manager = ScraperManager(DATA_DIR)
        self.analyzer = ForexAnalyzer()
        self.risk_manager = RiskManager(
            account_balance=account_balance,
            risk_percent=risk_percent
        )
        self.trade_executor = TradeExecutor(
            login=mt5_login,
            password=mt5_password,
            server=mt5_server,
            demo=demo_mode
        )
        
        self.min_confidence = min_confidence
        self.demo_mode = demo_mode
        self.daily_trades = 0
        self.max_daily_trades = 5
        self.daily_pnl = 0.0
        self.last_trade_time: Dict[str, datetime] = {}
        self.trade_cooldown_minutes = 60
        
        # Load pairs configuration
        self.pairs = self._load_pairs()
        
        # Trade log
        self.trade_log_file = DATA_DIR / "trade_log.json"
        self.trade_log = self._load_trade_log()
    
    def _load_pairs(self) -> Dict:
        """Load configured pairs"""
        pairs_file = DATA_DIR / "pairs.json"
        if pairs_file.exists():
            with open(pairs_file) as f:
                return json.load(f)
        return PAIR_CONFIGS
    
    def _load_trade_log(self) -> List:
        """Load trade log"""
        if self.trade_log_file.exists():
            with open(self.trade_log_file) as f:
                return json.load(f)
        return []
    
    def _save_trade_log(self):
        """Save trade log"""
        with open(self.trade_log_file, "w") as f:
            json.dump(self.trade_log, f, indent=2, default=str)
    
    async def run(self):
        """Main bot loop"""
        logger.info("Starting Trading Bot...")
        
        # Connect to MT5
        if not self.demo_mode:
            if not self.trade_executor.connect():
                logger.error("Failed to connect to MT5. Running in analysis-only mode.")
        
        try:
            while True:
                await self._trading_cycle()
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            self.trade_executor.disconnect()
    
    async def _trading_cycle(self):
        """Single trading cycle"""
        logger.info(f"Starting trading cycle at {datetime.now()}")
        
        # Check if we should trade
        if not self._should_trade():
            logger.info("Trading conditions not met, skipping cycle")
            return
        
        # Scrape news
        logger.info("Scraping news...")
        articles = await self.scraper_manager.scrape_all(list(self.pairs.keys()))
        logger.info(f"Scraped {len(articles)} articles")
        
        # Check for high-impact news
        if self._has_high_impact_news(articles):
            logger.warning("High-impact news detected, pausing trading")
            return
        
        # Analyze each pair
        for pair in self.pairs.keys():
            await self._analyze_and_trade(pair, articles)
        
        # Update account info
        if self.trade_executor.connected:
            account_info = self.trade_executor.get_account_info()
            if account_info:
                self.risk_manager.update_balance(account_info["balance"])
                logger.info(f"Account balance: {account_info['balance']}")
    
    async def _analyze_and_trade(self, pair: str, articles: list):
        """Analyze pair and execute trade if conditions met"""
        logger.info(f"Analyzing {pair}...")
        
        # Check cooldown
        if not self._check_cooldown(pair):
            logger.info(f"{pair}: In cooldown period, skipping")
            return
        
        # Get analysis
        analysis = await self.analyzer.analyze_pair(pair, articles)
        recommendation = await self.analyzer.get_trade_recommendation(pair, analysis)
        
        logger.info(f"{pair}: {recommendation.recommendation} ({recommendation.confidence}% confidence)")
        
        # Check if we should trade
        if not self._should_execute_trade(recommendation):
            logger.info(f"{pair}: Trade conditions not met")
            return
        
        # Calculate position size
        position = self.risk_manager.calculate_position_size(
            pair=pair,
            sl_pips=recommendation.stop_loss.get("pips", 30),
            tp_pips=recommendation.take_profit.get("pips", 60)
        )
        
        # Validate trade
        validation = self.risk_manager.validate_trade(
            pair=pair,
            sl_pips=recommendation.stop_loss.get("pips", 30),
            tp_pips=recommendation.take_profit.get("pips", 60)
        )
        
        if not validation["valid"]:
            logger.warning(f"{pair}: Trade validation failed: {validation['issues']}")
            return
        
        # Execute trade
        if self.demo_mode:
            logger.info(f"[DEMO] Would execute: {recommendation.recommendation} {pair} @ {position.lots} lots")
            self._log_trade(pair, recommendation, position, demo=True)
        else:
            order_type = OrderType.BUY if recommendation.recommendation == "BUY" else OrderType.SELL
            
            result = self.trade_executor.execute_trade(
                pair=pair,
                order_type=order_type,
                lots=position.lots,
                sl_pips=recommendation.stop_loss.get("pips", 30),
                tp_pips=recommendation.take_profit.get("pips", 60),
                comment=f"AI Trade - {recommendation.timeframe}"
            )
            
            if result.success:
                logger.info(f"{pair}: Trade executed successfully - Order #{result.order_id}")
                self._log_trade(pair, recommendation, position, demo=False, order_id=result.order_id)
                self.daily_trades += 1
                self.last_trade_time[pair] = datetime.now()
            else:
                logger.error(f"{pair}: Trade failed - {result.message}")
    
    def _should_trade(self) -> bool:
        """Check if trading should continue"""
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            logger.info("Daily trade limit reached")
            return False
        
        # Check daily loss limit
        if self.risk_manager.should_stop_trading(self.daily_pnl):
            logger.warning("Daily loss limit reached, stopping trading")
            return False
        
        # Check if market is open (simplified - add proper market hours check)
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            logger.info("Market closed (weekend)")
            return False
        
        return True
    
    def _should_execute_trade(self, recommendation: TradeRecommendation) -> bool:
        """Check if trade should be executed"""
        # Check recommendation
        if recommendation.recommendation == "HOLD":
            return False
        
        # Check confidence
        if recommendation.confidence < self.min_confidence:
            return False
        
        # Check risk-reward
        sl_pips = recommendation.stop_loss.get("pips", 0)
        tp_pips = recommendation.take_profit.get("pips", 0)
        
        if sl_pips <= 0 or tp_pips <= 0:
            return False
        
        if tp_pips / sl_pips < 1.5:
            return False
        
        return True
    
    def _check_cooldown(self, pair: str) -> bool:
        """Check if pair is in cooldown period"""
        if pair not in self.last_trade_time:
            return True
        
        elapsed = datetime.now() - self.last_trade_time[pair]
        return elapsed > timedelta(minutes=self.trade_cooldown_minutes)
    
    def _has_high_impact_news(self, articles: list) -> bool:
        """Check if there's high-impact news in the next hour"""
        for article in articles:
            if article.importance == "high":
                for event in self.HIGH_IMPACT_EVENTS:
                    if event.lower() in article.title.lower():
                        return True
        return False
    
    def _log_trade(
        self,
        pair: str,
        recommendation: TradeRecommendation,
        position,
        demo: bool = True,
        order_id: Optional[int] = None
    ):
        """Log trade to file"""
        trade_entry = {
            "timestamp": datetime.now().isoformat(),
            "pair": pair,
            "action": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "timeframe": recommendation.timeframe,
            "lots": position.lots,
            "sl_pips": recommendation.stop_loss.get("pips", 0),
            "tp_pips": recommendation.take_profit.get("pips", 0),
            "risk_amount": position.risk_amount,
            "reasoning": recommendation.reasoning,
            "demo": demo,
            "order_id": order_id
        }
        
        self.trade_log.append(trade_entry)
        self._save_trade_log()
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of trading day)"""
        self.daily_trades = 0
        self.daily_pnl = 0.0
        logger.info("Daily stats reset")


async def main():
    """Main entry point"""
    # Load configuration from environment or config file
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bot = TradingBot(
        mt5_login=int(os.getenv("MT5_LOGIN", 0)),
        mt5_password=os.getenv("MT5_PASSWORD", ""),
        mt5_server=os.getenv("MT5_SERVER", ""),
        account_balance=float(os.getenv("ACCOUNT_BALANCE", 10000)),
        risk_percent=float(os.getenv("RISK_PERCENT", 1.0)),
        min_confidence=int(os.getenv("MIN_CONFIDENCE", 60)),
        demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true"
    )
    
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
