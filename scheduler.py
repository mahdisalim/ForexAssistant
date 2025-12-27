"""
Scheduler for automated scraping and analysis
"""
import asyncio
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path

from config.settings import DATA_DIR, SCRAPE_INTERVAL_MINUTES
from scrapers import ScraperManager
from llm.analyzer import ForexAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
scraper_manager = ScraperManager(DATA_DIR)
analyzer = ForexAnalyzer()


async def daily_analysis_job():
    """Run daily analysis job"""
    logger.info(f"Starting daily analysis job at {datetime.now()}")
    
    try:
        # Load pairs
        import json
        pairs_file = DATA_DIR / "pairs.json"
        if pairs_file.exists():
            with open(pairs_file) as f:
                pairs = list(json.load(f).keys())
        else:
            pairs = ["EURUSD", "XAUUSD", "GBPUSD", "USDJPY"]
        
        # Scrape news
        logger.info("Scraping news from all sources...")
        articles = await scraper_manager.scrape_all(pairs)
        logger.info(f"Scraped {len(articles)} articles")
        
        # Generate analysis for each pair
        results = []
        for pair in pairs:
            logger.info(f"Analyzing {pair}...")
            analysis = await analyzer.analyze_pair(pair, articles)
            recommendation = await analyzer.get_trade_recommendation(pair, analysis)
            
            results.append({
                "pair": pair,
                "sentiment": analysis.sentiment,
                "recommendation": recommendation.recommendation,
                "confidence": recommendation.confidence,
                "timeframe": recommendation.timeframe,
                "sl_pips": recommendation.stop_loss.get("pips", 0),
                "tp_pips": recommendation.take_profit.get("pips", 0)
            })
            
            logger.info(f"{pair}: {recommendation.recommendation} ({recommendation.confidence}% confidence)")
        
        # Save daily report
        report_file = DATA_DIR / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "results": results
            }, f, indent=2)
        
        logger.info(f"Daily report saved to {report_file}")
        
    except Exception as e:
        logger.error(f"Error in daily analysis job: {e}")


def run_async_job():
    """Wrapper to run async job"""
    asyncio.run(daily_analysis_job())


def main():
    """Run scheduler"""
    logger.info("Starting Forex Analysis Scheduler...")
    
    # Schedule jobs
    schedule.every(SCRAPE_INTERVAL_MINUTES).minutes.do(run_async_job)
    schedule.every().day.at("06:00").do(run_async_job)  # Morning analysis
    schedule.every().day.at("14:00").do(run_async_job)  # Afternoon analysis
    
    # Run immediately on start
    run_async_job()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
