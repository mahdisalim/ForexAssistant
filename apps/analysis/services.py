"""
Analysis Services - Integration with scrapers, AI analyzer, and chart image analysis
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .chart_service import get_chart_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for market analysis and news aggregation"""
    
    def __init__(self):
        self.scrapers_initialized = False
        self.analyzer_initialized = False
        self.chart_analyzer_initialized = False
    
    def _init_scrapers(self):
        """Lazy initialization of scrapers"""
        if not self.scrapers_initialized:
            try:
                import sys
                sys.path.insert(0, '/app')
                from scrapers.scraper_manager import ScraperManager
                
                data_dir = Path('/app/data')
                data_dir.mkdir(exist_ok=True)
                
                self.scraper_manager = ScraperManager(data_dir)
                self.scrapers_initialized = True
                logger.info("Scrapers initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize scrapers: {e}")
                raise
    
    def _init_analyzer(self):
        """Lazy initialization of AI analyzer"""
        if not self.analyzer_initialized:
            try:
                import sys
                sys.path.insert(0, '/app')
                from llm.analyzer import ForexAnalyzer
                
                self.analyzer = ForexAnalyzer()
                self.analyzer_initialized = True
                logger.info("Analyzer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize analyzer: {e}")
                raise
    
    def _init_chart_analyzer(self):
        """Lazy initialization of chart image analyzer"""
        if not self.chart_analyzer_initialized:
            try:
                import sys
                sys.path.insert(0, '/app')
                from llm.chart_analyzer import ChartImageAnalyzer
                
                self.chart_analyzer = ChartImageAnalyzer()
                self.chart_analyzer_initialized = True
                logger.info("Chart analyzer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize chart analyzer: {e}")
                raise
    
    async def generate_daily_summary(
        self, 
        timeframe: str = 'H1', 
        asset: str = 'USD', 
        lang: str = 'fa'
    ) -> Dict:
        """
        Generate daily market summary by:
        1. Scraping news from 5 sources
        2. Using AI to generate comprehensive summary
        
        Args:
            timeframe: Trading timeframe (H1, H4, D1, etc.)
            asset: Asset to focus on (USD, EUR, GBP, etc.)
            lang: Language for summary (fa, en, ar, etc.)
        
        Returns:
            Dictionary with summary and metadata
        """
        try:
            # Initialize components
            self._init_scrapers()
            self._init_analyzer()
            
            # Step 1: Scrape news from all sources
            logger.info("Starting news scraping from 5 sources...")
            articles = await self.scraper_manager.scrape_all()
            
            if not articles:
                return {
                    'generated_at': datetime.now().isoformat(),
                    'articles_count': 0,
                    'timeframe': timeframe,
                    'asset': asset,
                    'lang': lang,
                    'summary': 'No news articles found. Please try again later.',
                    'sources': []
                }
            
            # Step 2: Generate AI summary
            logger.info(f"Generating AI summary with {len(articles)} articles...")
            summary_text = await self.analyzer.generate_daily_summary(
                articles=articles,
                timeframe=timeframe,
                asset=asset,
                lang=lang
            )
            
            # Get unique sources
            sources = list(set([article.source for article in articles]))
            
            return {
                'generated_at': datetime.now().isoformat(),
                'articles_count': len(articles),
                'timeframe': timeframe,
                'asset': asset,
                'lang': lang,
                'summary': summary_text,
                'sources': sources,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}", exc_info=True)
            return {
                'generated_at': datetime.now().isoformat(),
                'articles_count': 0,
                'timeframe': timeframe,
                'asset': asset,
                'lang': lang,
                'summary': f'Error generating summary: {str(e)}',
                'sources': [],
                'success': False,
                'error': str(e)
            }
    
    async def analyze_pair(
        self,
        pair: str,
        timeframe: str = 'H1',
        trading_style: str = 'day'
    ) -> Dict:
        """
        Analyze a specific currency pair with full AI analysis and trade recommendation
        
        Args:
            pair: Currency pair (e.g., EURUSD)
            timeframe: Trading timeframe
            trading_style: Trading style (scalp, day, swing, position)
        
        Returns:
            Dictionary with analysis and recommendation
        """
        try:
            self._init_scrapers()
            self._init_analyzer()
            
            # Scrape news
            logger.info(f"Scraping news for {pair}...")
            articles = await self.scraper_manager.scrape_all(currency_pairs=[pair])
            
            if not articles:
                logger.warning(f"No articles found for {pair}")
                return {
                    'pair': pair,
                    'analysis': {
                        'sentiment': 'Neutral',
                        'sentiment_score': 50,
                        'key_factors': ['اخبار مرتبط یافت نشد'],
                        'summary': 'No relevant news found',
                    },
                    'recommendation': {
                        'recommendation': 'WAIT',
                        'confidence': 0,
                        'timeframe': timeframe,
                        'trading_style': trading_style,
                        'reasoning': 'عدم وجود اخبار کافی برای تحلیل',
                        'stop_loss': {'pips': 0, 'description': 'منتظر اخبار'},
                        'take_profit': {'pips': 0, 'description': 'منتظر اخبار'}
                    },
                    'generated_at': datetime.now().isoformat()
                }
            
            # Analyze with AI
            logger.info(f"Analyzing {pair} with {len(articles)} articles...")
            analysis = await self.analyzer.analyze_pair(
                pair=pair,
                articles=articles,
                timeframe=timeframe,
                trading_style=trading_style
            )
            
            # Get trade recommendation
            logger.info(f"Getting trade recommendation for {pair}...")
            recommendation = await self.analyzer.get_trade_recommendation(
                pair=pair,
                analysis=analysis,
                timeframe=timeframe,
                trading_style=trading_style
            )
            
            return {
                'pair': pair,
                'analysis': {
                    'sentiment': analysis.sentiment,
                    'sentiment_score': analysis.confidence,
                    'summary': analysis.summary,
                    'key_factors': analysis.key_factors,
                    'technical_outlook': analysis.technical_outlook,
                    'risk_factors': analysis.risk_factors,
                    'sources_count': analysis.sources_count,
                },
                'recommendation': {
                    'recommendation': recommendation.recommendation,
                    'confidence': recommendation.confidence,
                    'timeframe': recommendation.timeframe,
                    'trading_style': trading_style,
                    'entry_zone': recommendation.entry_zone,
                    'stop_loss': recommendation.stop_loss,
                    'take_profit': recommendation.take_profit,
                    'risk_reward_ratio': recommendation.risk_reward_ratio,
                    'reasoning': recommendation.reasoning,
                    'key_levels': recommendation.key_levels,
                    'invalidation': recommendation.invalidation,
                    'news_to_watch': recommendation.news_to_watch,
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pair {pair}: {e}", exc_info=True)
            return {
                'pair': pair,
                'analysis': {
                    'sentiment': 'Unknown',
                    'sentiment_score': 0,
                    'key_factors': [f'خطا: {str(e)}'],
                    'summary': f'Error: {str(e)}',
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 0,
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                    'reasoning': f'خطا در تحلیل: {str(e)}',
                    'stop_loss': {'pips': 0, 'description': 'خطا'},
                    'take_profit': {'pips': 0, 'description': 'خطا'}
                },
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def analyze_chart_image(
        self,
        pair: str,
        image_data: str,
        timeframe: str = 'H1',
        trading_style: str = 'day'
    ) -> Dict:
        """
        Analyze a chart image using AI vision
        
        Args:
            pair: Currency pair
            image_data: Base64 encoded chart image
            timeframe: Trading timeframe
            trading_style: Trading style
        
        Returns:
            Dictionary with analysis and recommendation
        """
        try:
            self._init_chart_analyzer()
            
            logger.info(f"Analyzing chart image for {pair}...")
            result = await self.chart_analyzer.analyze_chart_image(
                pair=pair,
                image_data=image_data,
                timeframe=timeframe,
                trading_style=trading_style
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing chart image for {pair}: {e}", exc_info=True)
            return {
                'pair': pair,
                'analysis': {
                    'sentiment': 'Unknown',
                    'sentiment_score': 0,
                    'key_factors': [f'خطا: {str(e)}'],
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 0,
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                    'reasoning': f'خطا در تحلیل تصویر: {str(e)}',
                    'stop_loss': {'pips': 0, 'description': 'خطا'},
                    'take_profit': {'pips': 0, 'description': 'خطا'}
                },
                'generated_at': datetime.now().isoformat()
            }
    
    async def auto_chart_analysis(
        self,
        pair: str,
        timeframe: str = 'H1',
        trading_style: str = 'day',
        multi_timeframe: bool = False,
        timeframes: list = None
    ) -> Dict:
        """
        Automatically capture chart and analyze with AI
        This is the main method called by the refresh button
        
        Args:
            pair: Currency pair
            timeframe: Trading timeframe (used if multi_timeframe=False)
            trading_style: Trading style
            multi_timeframe: If True, capture and analyze multiple timeframes
            timeframes: List of timeframes to analyze (optional, auto-selected if None)
        
        Returns:
            Dictionary with analysis and recommendation
        """
        try:
            # Get chart service
            chart_service = get_chart_service()
            
            # Multi-timeframe analysis
            if multi_timeframe:
                logger.info(f"Attempting multi-timeframe chart capture for {pair}...")
                chart_images = await chart_service.capture_multi_timeframe_charts(
                    pair=pair,
                    timeframes=timeframes,
                    trading_style=trading_style
                )
                
                # Filter out failed captures
                valid_charts = {tf: img for tf, img in chart_images.items() if img is not None}
                
                if valid_charts:
                    logger.info(f"Captured {len(valid_charts)} timeframes, sending to AI for multi-timeframe analysis...")
                    try:
                        self._init_chart_analyzer()
                        
                        result = await self.chart_analyzer.analyze_multi_timeframe_charts(
                            pair=pair,
                            chart_images=valid_charts,
                            trading_style=trading_style
                        )
                        
                        if result.get('error') or result.get('recommendation', {}).get('confidence', 0) == 0:
                            logger.warning(f"AI multi-timeframe analysis returned error, using config-based")
                            return await self._generate_config_based_analysis(pair, timeframe, trading_style)
                        
                        # Save to database (use primary timeframe)
                        primary_tf = list(valid_charts.keys())[0] if valid_charts else timeframe
                        await self._save_chart_analysis(pair, primary_tf, trading_style, result)
                        
                        return result
                    except Exception as ai_error:
                        logger.warning(f"AI multi-timeframe analysis failed: {ai_error}, using config-based")
                        return await self._generate_config_based_analysis(pair, timeframe, trading_style)
                else:
                    logger.warning(f"No charts captured for multi-timeframe analysis, using config-based")
                    return await self._generate_config_based_analysis(pair, timeframe, trading_style)
            
            # Single timeframe analysis (original behavior)
            else:
                logger.info(f"Attempting automatic chart capture for {pair} on {timeframe}...")
                image_data = await chart_service.capture_chart_screenshot(
                    pair=pair,
                    timeframe=timeframe,
                    trading_style=trading_style
                )
                
                if image_data:
                    logger.info(f"Chart captured, sending to AI for analysis...")
                    try:
                        self._init_chart_analyzer()
                        
                        result = await self.chart_analyzer.analyze_chart_image(
                            pair=pair,
                            image_data=image_data,
                            timeframe=timeframe,
                            trading_style=trading_style
                        )
                        
                        if result.get('error') or result.get('recommendation', {}).get('confidence', 0) == 0:
                            logger.warning(f"AI analysis returned error or low confidence, using config-based")
                            return await self._generate_config_based_analysis(pair, timeframe, trading_style)
                        
                        await self._save_chart_analysis(pair, timeframe, trading_style, result)
                        
                        return result
                    except Exception as ai_error:
                        logger.warning(f"AI analysis failed: {ai_error}, using config-based analysis")
                        return await self._generate_config_based_analysis(pair, timeframe, trading_style)
                else:
                    logger.info(f"No chart image, using config-based analysis for {pair}...")
                    return await self._generate_config_based_analysis(pair, timeframe, trading_style)
                
        except Exception as e:
            logger.error(f"Auto chart analysis error for {pair}: {e}", exc_info=True)
            return {
                'pair': pair,
                'analysis': {
                    'sentiment': 'Unknown',
                    'sentiment_score': 0,
                    'key_factors': [f'خطا: {str(e)}'],
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 0,
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                    'reasoning': f'خطا در تحلیل: {str(e)}',
                    'stop_loss': {'pips': 0, 'description': 'خطا'},
                    'take_profit': {'pips': 0, 'description': 'خطا'}
                },
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _save_chart_analysis(
        self,
        pair: str,
        timeframe: str,
        trading_style: str,
        result: Dict
    ):
        """Save chart analysis to database"""
        try:
            from .models import CurrencyPair, ChartAnalysis
            
            # Get or create currency pair
            pair_obj, _ = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: CurrencyPair.objects.get_or_create(symbol=pair.upper())
            )
            
            analysis = result.get('analysis', {})
            rec = result.get('recommendation', {})
            
            # Create chart analysis record
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ChartAnalysis.objects.create(
                    pair=pair_obj,
                    timeframe=timeframe,
                    trading_style=trading_style,
                    sentiment=analysis.get('sentiment', 'Neutral'),
                    sentiment_score=analysis.get('sentiment_score', 0),
                    trend=analysis.get('trend', 'sideways'),
                    recommendation=rec.get('recommendation', 'WAIT'),
                    confidence=rec.get('confidence', 0),
                    entry_min=str(rec.get('entry_zone', {}).get('min', '')),
                    entry_max=str(rec.get('entry_zone', {}).get('max', '')),
                    stop_loss_price=str(rec.get('stop_loss', {}).get('price', '')),
                    stop_loss_pips=rec.get('stop_loss', {}).get('pips', 0) or 0,
                    take_profit_price=str(rec.get('take_profit', {}).get('price', '')),
                    take_profit_pips=rec.get('take_profit', {}).get('pips', 0) or 0,
                    risk_reward_ratio=rec.get('risk_reward_ratio', 0) or 0,
                    key_factors=analysis.get('key_factors', []),
                    support_levels=analysis.get('support_levels', []),
                    resistance_levels=analysis.get('resistance_levels', []),
                    reasoning=rec.get('reasoning', ''),
                    invalidation=rec.get('invalidation', ''),
                    raw_response=result
                )
            )
            logger.info(f"Chart analysis saved for {pair}")
        except Exception as e:
            logger.error(f"Failed to save chart analysis: {e}")
    
    async def _generate_config_based_analysis(
        self,
        pair: str,
        timeframe: str,
        trading_style: str
    ) -> Dict:
        """Generate analysis based on pair configuration when chart image not available"""
        try:
            # Get pair config
            import sys
            sys.path.insert(0, '/app')
            from config.settings import PAIR_CONFIGS
            
            config = PAIR_CONFIGS.get(pair.upper(), {
                'volatility': 'medium',
                'default_sl_pips': 30,
                'default_tp_pips': 60
            })
            
            sl_pips = config.get('default_sl_pips', 30)
            tp_pips = config.get('default_tp_pips', 60)
            volatility = config.get('volatility', 'medium')
            
            # Adjust based on trading style
            style_multipliers = {
                'scalp': 0.3,
                'day': 1.0,
                'swing': 2.5,
                'position': 5.0
            }
            multiplier = style_multipliers.get(trading_style, 1.0)
            
            adjusted_sl = int(sl_pips * multiplier)
            adjusted_tp = int(tp_pips * multiplier)
            rr_ratio = round(adjusted_tp / adjusted_sl, 2) if adjusted_sl > 0 else 0
            
            return {
                'pair': pair,
                'analysis': {
                    'sentiment': 'Neutral',
                    'sentiment_score': 50,
                    'trend': 'sideways',
                    'key_factors': [
                        f'نوسان: {volatility}',
                        f'تایم‌فریم: {timeframe}',
                        f'استایل: {trading_style}',
                        'برای تحلیل دقیق‌تر، تصویر چارت آپلود کنید'
                    ],
                    'support_levels': [],
                    'resistance_levels': [],
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 30,
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                    'entry_zone': {
                        'min': 'منتظر سیگنال',
                        'max': 'منتظر سیگنال',
                        'description': 'نیاز به تحلیل چارت'
                    },
                    'stop_loss': {
                        'pips': adjusted_sl,
                        'description': f'بر اساس تنظیمات {pair}'
                    },
                    'take_profit': {
                        'pips': adjusted_tp,
                        'description': f'بر اساس تنظیمات {pair}'
                    },
                    'risk_reward_ratio': rr_ratio,
                    'reasoning': 'تحلیل بر اساس تنظیمات پیش‌فرض جفت ارز. برای تحلیل دقیق‌تر از دکمه باز کردن چارت استفاده کنید و تصویر را آپلود کنید.',
                    'key_levels': [],
                    'invalidation': 'نیاز به بررسی چارت',
                },
                'generated_at': datetime.now().isoformat(),
                'source': 'config_based'
            }
            
        except Exception as e:
            logger.error(f"Config-based analysis error: {e}")
            return {
                'pair': pair,
                'analysis': {'sentiment': 'Unknown', 'sentiment_score': 0},
                'recommendation': {'recommendation': 'WAIT', 'confidence': 0},
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }


# Singleton instance
_analysis_service = None

def get_analysis_service() -> AnalysisService:
    """Get or create analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
