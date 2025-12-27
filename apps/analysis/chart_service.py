"""
Chart Service - Automatic TradingView chart screenshot capture
Uses Playwright for headless browser screenshot capture
"""
import base64
import logging
import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Playwright browser instance (singleton)
_browser = None
_playwright = None


class TradingViewChartService:
    """Service to capture TradingView chart images automatically"""
    
    # Timeframe mapping (MT4/MT5 to TradingView)
    TIMEFRAME_MAP = {
        'M1': '1',
        'M5': '5',
        'M15': '15',
        'M30': '30',
        'H1': '60',
        'H4': '240',
        'D1': 'D',
        'W1': 'W',
        'MN1': 'M',
    }
    
    def __init__(self):
        self.base_url = "https://s.tradingview.com/widgetembed/"
        self.chart_img_base = "https://www.tradingview.com/chart/"
    
    def get_tv_symbol(self, pair: str) -> str:
        """Convert pair to TradingView symbol format with database lookup + smart fallback"""
        pair = pair.upper().replace('/', '')
        
        # 1. Check database first for custom symbols
        try:
            from apps.analysis.models import CurrencyPair
            currency_pair = CurrencyPair.objects.filter(symbol=pair).first()
            if currency_pair and currency_pair.tradingview_symbol:
                return currency_pair.tradingview_symbol
        except Exception as e:
            logger.debug(f"Database lookup failed for {pair}: {e}")
        
        # 2. Smart auto-detection based on symbol patterns
        # Gold/Silver
        if pair in ['XAUUSD', 'GOLD']:
            return 'TVC:GOLD'
        elif pair in ['XAGUSD', 'SILVER']:
            return 'TVC:SILVER'
        
        # Crypto
        elif pair.startswith('BTC'):
            return f'BITSTAMP:{pair}'
        elif pair.startswith('ETH'):
            return f'BITSTAMP:{pair}'
        elif pair in ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD']:
            return f'BITSTAMP:{pair}'
        
        # Indices
        elif pair in ['SPX', 'SPX500', 'US500']:
            return 'SP:SPX'
        elif pair in ['DJI', 'US30']:
            return 'DJ:DJI'
        elif pair in ['NDX', 'NAS100', 'US100']:
            return 'NASDAQ:NDX'
        
        # Commodities
        elif pair in ['USOIL', 'WTIUSD']:
            return 'TVC:USOIL'
        elif pair in ['UKOIL', 'BRENTUSD']:
            return 'TVC:UKOIL'
        
        # Default: Forex pairs
        else:
            return f'FX:{pair}'
    
    def get_tv_interval(self, timeframe: str) -> str:
        """Convert timeframe to TradingView interval"""
        return self.TIMEFRAME_MAP.get(timeframe.upper(), '60')
    
    async def get_chart_image_url(
        self, 
        pair: str, 
        timeframe: str = 'H1',
        width: int = 800,
        height: int = 600
    ) -> str:
        """
        Generate TradingView chart image URL
        Uses TradingView's Mini Chart Widget which provides chart images
        """
        symbol = self.get_tv_symbol(pair)
        interval = self.get_tv_interval(timeframe)
        
        # TradingView Mini Chart Widget URL (provides chart image)
        chart_url = (
            f"https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget"
            f"&symbol={symbol}"
            f"&interval={interval}"
            f"&hidesidetoolbar=1"
            f"&symboledit=0"
            f"&saveimage=0"
            f"&toolbarbg=f1f3f6"
            f"&studies=[]"
            f"&theme=dark"
            f"&style=1"
            f"&timezone=Etc/UTC"
            f"&withdateranges=0"
            f"&showpopupbutton=0"
            f"&width={width}"
            f"&height={height}"
            f"&locale=en"
        )
        
        return chart_url
    
    async def capture_chart_screenshot(
        self,
        pair: str,
        timeframe: str = 'H1',
        trading_style: str = 'day'
    ) -> Optional[str]:
        """
        Capture single chart screenshot using Playwright headless browser
        Returns base64 encoded image data
        """
        global _browser, _playwright
        
        try:
            symbol = self.get_tv_symbol(pair)
            interval = self.get_tv_interval(timeframe)
            
            # Try Playwright first for real chart screenshot
            try:
                from playwright.async_api import async_playwright
                
                if _playwright is None:
                    _playwright = await async_playwright().start()
                    _browser = await _playwright.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox']
                    )
                
                page = await _browser.new_page(viewport={'width': 1400, 'height': 900})
                
                # TradingView widget URL with proper encoding
                widget_url = (
                    f"https://s.tradingview.com/widgetembed/"
                    f"?frameElementId=tradingview_widget"
                    f"&symbol={symbol}"
                    f"&interval={interval}"
                    f"&hidesidetoolbar=1"
                    f"&symboledit=0"
                    f"&saveimage=0"
                    f"&toolbarbg=1a1a2e"
                    f"&theme=dark"
                    f"&style=1"
                    f"&timezone=Etc%2FUTC"
                    f"&withdateranges=0"
                    f"&showpopupbutton=0"
                    f"&studies=%5B%5D"
                    f"&locale=en"
                )
                
                logger.info(f"Loading chart: {pair} ({symbol}) on {timeframe} ({interval})")
                await page.goto(widget_url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(4)  # Wait for chart to fully render
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(type='png', full_page=False)
                await page.close()
                
                image_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                logger.info(f"✓ Successfully captured chart for {pair} on {timeframe}")
                return image_data
                
            except ImportError:
                logger.warning("Playwright not available, trying alternative methods")
            except Exception as e:
                logger.error(f"Playwright screenshot failed for {pair} on {timeframe}: {e}")
            
            # Fallback: Try httpx for static chart images
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                chart_urls = [
                    f"https://chart.yahoo.com/z?s={pair}=X&t=1d&q=l&l=on&z=s&p=m50,m200",
                ]
                
                for url in chart_urls:
                    try:
                        response = await client.get(url)
                        content_type = response.headers.get('content-type', '')
                        
                        if response.status_code == 200 and 'image' in content_type:
                            image_data = base64.b64encode(response.content).decode('utf-8')
                            logger.info(f"Successfully captured chart for {pair} from {url[:50]}")
                            return image_data
                    except Exception as e:
                        logger.debug(f"Chart URL failed: {url[:50]} - {e}")
                        continue
            
            logger.info(f"No chart image available for {pair}, using config-based analysis")
            return None
                
        except Exception as e:
            logger.error(f"Chart capture error for {pair}: {e}")
            return None
    
    async def capture_multi_timeframe_charts(
        self,
        pair: str,
        timeframes: list = None,
        trading_style: str = 'day'
    ) -> Dict[str, Optional[str]]:
        """
        Capture multiple timeframe charts for comprehensive analysis
        Returns dict with timeframe as key and base64 image data as value
        """
        if timeframes is None:
            # Default multi-timeframe setup based on trading style
            if trading_style == 'scalp':
                timeframes = ['M5', 'M15', 'H1']
            elif trading_style == 'day':
                timeframes = ['H1', 'H4', 'D1']
            elif trading_style == 'swing':
                timeframes = ['H4', 'D1', 'W1']
            else:  # position
                timeframes = ['D1', 'W1', 'MN1']
        
        results = {}
        for tf in timeframes:
            logger.info(f"Capturing {pair} on {tf}...")
            image_data = await self.capture_chart_screenshot(pair, tf, trading_style)
            results[tf] = image_data
            if image_data:
                logger.info(f"✓ {pair} {tf} captured successfully")
            else:
                logger.warning(f"✗ {pair} {tf} capture failed")
            
            # Small delay between captures to avoid rate limiting
            await asyncio.sleep(1)
        
        return results
    
    def get_chart_description(self, pair: str, timeframe: str) -> str:
        """Generate a text description for AI when image not available"""
        symbol = self.get_tv_symbol(pair)
        return f"""
        Currency Pair: {pair}
        TradingView Symbol: {symbol}
        Timeframe: {timeframe}
        
        Please analyze this forex pair based on:
        1. Current market conditions
        2. Technical analysis principles
        3. Common support/resistance levels
        4. Trend analysis
        
        Provide specific entry, stop loss, and take profit levels.
        """
    
    def get_chart_embed_html(
        self,
        pair: str,
        timeframe: str = 'H1',
        width: int = 800,
        height: int = 600
    ) -> str:
        """Generate TradingView widget embed HTML"""
        symbol = self.get_tv_symbol(pair)
        interval = self.get_tv_interval(timeframe)
        
        return f'''
        <div class="tradingview-widget-container" id="tv-chart-{pair}">
            <div id="tradingview_{pair}"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "width": {width},
                "height": {height},
                "symbol": "{symbol}",
                "interval": "{interval}",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "allow_symbol_change": false,
                "container_id": "tradingview_{pair}"
            }});
            </script>
        </div>
        '''


# Singleton instance
_chart_service = None

def get_chart_service() -> TradingViewChartService:
    """Get or create chart service instance"""
    global _chart_service
    if _chart_service is None:
        _chart_service = TradingViewChartService()
    return _chart_service
