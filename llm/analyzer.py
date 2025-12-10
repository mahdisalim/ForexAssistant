"""
Forex Analyzer - AI-powered market analysis
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
from pydantic import BaseModel

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, PAIR_CONFIGS
from config.timeframes import TIMEFRAME_NAMES, TRADING_STYLES, get_mtf_timeframes, calculate_mtf_score
from scrapers.base_scraper import NewsArticle
from .prompts import (
    ANALYSIS_PROMPT, TRADE_SUGGESTION_PROMPT, SUMMARY_PROMPT_FA, SUMMARY_PROMPT_EN,
    PAIR_CLASSIFIER_PROMPT, MULTI_TIMEFRAME_PROMPT, TIMEFRAME_SPECIFIC_PROMPT,
    TIMEFRAME_GUIDELINES
)

logger = logging.getLogger(__name__)


class TradeRecommendation(BaseModel):
    """Model for trade recommendation"""
    pair: str
    recommendation: str  # BUY, SELL, HOLD
    confidence: int
    timeframe: str
    entry_zone: Dict[str, str]
    stop_loss: Dict[str, Any]
    take_profit: Dict[str, Any]
    risk_reward_ratio: float
    reasoning: str
    key_levels: List[str]
    invalidation: str
    news_to_watch: List[str]
    generated_at: datetime = None
    
    def __init__(self, **data):
        if 'generated_at' not in data or data['generated_at'] is None:
            data['generated_at'] = datetime.now()
        super().__init__(**data)


class MarketAnalysis(BaseModel):
    """Model for market analysis"""
    pair: str
    sentiment: str  # Bullish, Bearish, Neutral
    confidence: int
    summary: str
    key_factors: List[str]
    technical_outlook: str
    risk_factors: List[str]
    sources_count: int
    generated_at: datetime = None
    
    def __init__(self, **data):
        if 'generated_at' not in data or data['generated_at'] is None:
            data['generated_at'] = datetime.now()
        super().__init__(**data)


class TimeframeAnalysis(BaseModel):
    """Model for single timeframe analysis"""
    timeframe: str
    trend: str  # bullish, bearish, neutral
    strength: str  # strong, moderate, weak
    support_levels: List[str] = []
    resistance_levels: List[str] = []
    momentum: str  # increasing, decreasing, flat
    bias_score: int = 50


class MultiTimeframeAnalysis(BaseModel):
    """Model for multi-timeframe analysis"""
    pair: str
    primary_timeframe: str
    timeframes_analyzed: List[str]
    timeframe_details: Dict[str, TimeframeAnalysis]
    confluence: Dict[str, Any]
    overall_bias: str
    confidence: int
    trade_recommendation: Dict[str, Any]
    generated_at: datetime = None
    
    def __init__(self, **data):
        if 'generated_at' not in data or data['generated_at'] is None:
            data['generated_at'] = datetime.now()
        super().__init__(**data)


class ForexAnalyzer:
    """AI-powered forex market analyzer"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.model = OPENAI_MODEL
    
    # Trading style configurations - Enhanced
    TRADING_STYLES = {
        'scalp': {
            'name': 'Scalping',
            'name_fa': 'اسکالپ',
            'sl_range': (10, 20),
            'tp_range': (15, 30),
            'sl_multiplier': 0.5,
            'tp_multiplier': 0.5,
            'timeframes': ['M1', 'M5', 'M15'],
            'min_rr': 1.5,
            'duration': 'minutes to hours',
            'description': 'Quick trades with tight stops. Focus on momentum and quick profits.'
        },
        'day': {
            'name': 'Day Trading',
            'name_fa': 'روزانه',
            'sl_range': (20, 40),
            'tp_range': (40, 80),
            'sl_multiplier': 1.0,
            'tp_multiplier': 1.0,
            'timeframes': ['M15', 'H1', 'H4'],
            'min_rr': 2.0,
            'duration': 'hours to 1 day',
            'description': 'Intraday trades closed before market close. Focus on daily trends.'
        },
        'swing': {
            'name': 'Swing Trading',
            'name_fa': 'سوئینگ',
            'sl_range': (50, 100),
            'tp_range': (100, 200),
            'sl_multiplier': 2.0,
            'tp_multiplier': 2.5,
            'timeframes': ['H4', 'D1', 'W1'],
            'min_rr': 2.0,
            'duration': 'days to weeks',
            'description': 'Multi-day trades capturing larger moves. Focus on swing highs/lows.'
        },
        'position': {
            'name': 'Position Trading',
            'name_fa': 'پوزیشن',
            'sl_range': (100, 200),
            'tp_range': (200, 500),
            'sl_multiplier': 3.0,
            'tp_multiplier': 4.0,
            'timeframes': ['D1', 'W1', 'MN1'],
            'min_rr': 2.5,
            'duration': 'weeks to months',
            'description': 'Long-term trades based on fundamental analysis. Focus on major trends.'
        }
    }
    
    def _get_style_params(self, trading_style: str) -> str:
        """Get formatted trading style parameters for prompts"""
        style = self.TRADING_STYLES.get(trading_style, self.TRADING_STYLES['day'])
        return f"""
- Style: {style['name']}
- Recommended SL Range: {style['sl_range'][0]}-{style['sl_range'][1]} pips
- Recommended TP Range: {style['tp_range'][0]}-{style['tp_range'][1]} pips
- Minimum R:R Ratio: 1:{style['min_rr']}
- Typical Duration: {style['duration']}
- Recommended Timeframes: {', '.join(style['timeframes'])}
- Description: {style['description']}
"""

    async def analyze_pair(self, pair: str, articles: List[NewsArticle], timeframe: str = "H1", trading_style: str = "day") -> MarketAnalysis:
        """Analyze market for a specific currency pair with timeframe and trading style context"""
        # Filter articles for this pair
        relevant_articles = [a for a in articles if pair in a.currency_pairs or not a.currency_pairs]
        
        style_config = self.TRADING_STYLES.get(trading_style, self.TRADING_STYLES['day'])
        
        if not relevant_articles:
            return MarketAnalysis(
                pair=pair,
                sentiment="Neutral",
                confidence=0,
                summary="No relevant news found for this pair.",
                key_factors=[],
                technical_outlook="Insufficient data",
                risk_factors=["No recent news available"],
                sources_count=0
            )
        
        # Prepare articles text
        articles_text = self._format_articles(relevant_articles[:10])  # Limit to 10 articles
        
        # Get timeframes for this trading style
        style_timeframes = style_config.get('timeframes', ['H1'])
        
        # Generate analysis with full context
        prompt = ANALYSIS_PROMPT.format(
            articles=articles_text,
            pair=pair,
            trading_style=style_config['name'],
            timeframe=timeframe,
            timeframes=', '.join(style_timeframes)
        )
        
        system_prompt = f"""You are an expert forex market analyst specializing in {style_config['name']} trading.
Your analysis should be optimized for {timeframe} timeframe traders.
Provide actionable insights with specific price levels and clear trade setups.
Consider multi-timeframe analysis using: {', '.join(style_timeframes)}."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the response
            analysis = self._parse_analysis(pair, analysis_text, len(relevant_articles))
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing pair {pair}: {e}")
            return MarketAnalysis(
                pair=pair,
                sentiment="Unknown",
                confidence=0,
                summary=f"Error generating analysis: {str(e)}",
                key_factors=[],
                technical_outlook="Error",
                risk_factors=["Analysis failed"],
                sources_count=len(relevant_articles)
            )
    
    async def get_trade_recommendation(self, pair: str, analysis: MarketAnalysis, timeframe: str = "H1", trading_style: str = "day", timeframes: List[str] = None) -> TradeRecommendation:
        """Generate trade recommendation based on analysis with timeframe and trading style"""
        pair_config = PAIR_CONFIGS.get(pair, {
            "volatility": "medium",
            "default_sl_pips": 30,
            "default_tp_pips": 60
        })
        
        style_config = self.TRADING_STYLES.get(trading_style, self.TRADING_STYLES['day'])
        
        # Get timeframes list
        tf_list = timeframes if timeframes else style_config.get('timeframes', [timeframe])
        
        # Adjust SL/TP based on trading style
        adjusted_sl = int(pair_config.get("default_sl_pips", 30) * style_config['sl_multiplier'])
        adjusted_tp = int(pair_config.get("default_tp_pips", 60) * style_config['tp_multiplier'])
        
        # Get style parameters for prompt
        style_params = self._get_style_params(trading_style)
        
        prompt = TRADE_SUGGESTION_PROMPT.format(
            analysis=analysis.summary,
            pair=pair,
            trading_style=style_config['name'],
            timeframe=timeframe,
            timeframes=', '.join(tf_list),
            volatility=pair_config.get("volatility", "medium"),
            default_sl=adjusted_sl,
            default_tp=adjusted_tp,
            style_params=style_params
        )
        
        system_prompt = f"""You are an expert forex trading advisor specializing in {style_config['name']}.
You MUST respond with valid JSON only. No markdown, no explanations outside JSON.
Provide specific, actionable trade recommendations optimized for {timeframe} timeframe.
Consider the full analysis context and multi-timeframe alignment."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            trade_data = self._extract_json(response_text)
            
            if trade_data:
                return TradeRecommendation(
                    pair=pair,
                    recommendation=trade_data.get("recommendation", "HOLD"),
                    confidence=trade_data.get("confidence", 50),
                    timeframe=trade_data.get("timeframe", "H1"),
                    entry_zone=trade_data.get("entry_zone", {"type": "market", "price_description": "Current market price"}),
                    stop_loss=trade_data.get("stop_loss", {"pips": pair_config["default_sl_pips"], "description": "Default SL"}),
                    take_profit=trade_data.get("take_profit", {"pips": pair_config["default_tp_pips"], "description": "Default TP"}),
                    risk_reward_ratio=trade_data.get("risk_reward_ratio", 1.5),
                    reasoning=trade_data.get("reasoning", "Based on market analysis"),
                    key_levels=trade_data.get("key_levels", []),
                    invalidation=trade_data.get("invalidation", "Price breaks key levels"),
                    news_to_watch=trade_data.get("news_to_watch", [])
                )
            else:
                raise ValueError("Could not parse trade recommendation")
                
        except Exception as e:
            logger.error(f"Error generating trade recommendation for {pair}: {e}")
            return TradeRecommendation(
                pair=pair,
                recommendation="HOLD",
                confidence=0,
                timeframe="H1",
                entry_zone={"type": "none", "price_description": "No trade recommended"},
                stop_loss={"pips": 0, "description": "N/A"},
                take_profit={"pips": 0, "description": "N/A"},
                risk_reward_ratio=0,
                reasoning=f"Error generating recommendation: {str(e)}",
                key_levels=[],
                invalidation="N/A",
                news_to_watch=[]
            )
    
    # Asset configurations for market overview - multilingual
    ASSET_INFO = {
        # Currencies
        "USD": {"name_fa": "دلار آمریکا", "name_en": "US Dollar", "type": "currency", "country_fa": "آمریکا", "country_en": "USA"},
        "EUR": {"name_fa": "یورو", "name_en": "Euro", "type": "currency", "country_fa": "اتحادیه اروپا", "country_en": "Eurozone"},
        "GBP": {"name_fa": "پوند انگلیس", "name_en": "British Pound", "type": "currency", "country_fa": "انگلیس", "country_en": "UK"},
        "JPY": {"name_fa": "ین ژاپن", "name_en": "Japanese Yen", "type": "currency", "country_fa": "ژاپن", "country_en": "Japan"},
        "CHF": {"name_fa": "فرانک سوئیس", "name_en": "Swiss Franc", "type": "currency", "country_fa": "سوئیس", "country_en": "Switzerland"},
        "AUD": {"name_fa": "دلار استرالیا", "name_en": "Australian Dollar", "type": "currency", "country_fa": "استرالیا", "country_en": "Australia"},
        "CAD": {"name_fa": "دلار کانادا", "name_en": "Canadian Dollar", "type": "currency", "country_fa": "کانادا", "country_en": "Canada"},
        "NZD": {"name_fa": "دلار نیوزیلند", "name_en": "New Zealand Dollar", "type": "currency", "country_fa": "نیوزیلند", "country_en": "New Zealand"},
        "CNY": {"name_fa": "یوان چین", "name_en": "Chinese Yuan", "type": "currency", "country_fa": "چین", "country_en": "China"},
        # Commodities
        "XAU": {"name_fa": "طلا", "name_en": "Gold", "type": "commodity", "country_fa": "جهانی", "country_en": "Global"},
        "XAG": {"name_fa": "نقره", "name_en": "Silver", "type": "commodity", "country_fa": "جهانی", "country_en": "Global"},
        "OIL": {"name_fa": "نفت", "name_en": "Crude Oil", "type": "commodity", "country_fa": "جهانی", "country_en": "Global"},
        # Indices
        "SPX": {"name_fa": "اس اند پی ۵۰۰", "name_en": "S&P 500", "type": "index", "country_fa": "آمریکا", "country_en": "USA"},
        "DJI": {"name_fa": "داوجونز", "name_en": "Dow Jones", "type": "index", "country_fa": "آمریکا", "country_en": "USA"},
        "NDX": {"name_fa": "نزدک", "name_en": "NASDAQ", "type": "index", "country_fa": "آمریکا", "country_en": "USA"},
        "FTSE": {"name_fa": "فوتسی ۱۰۰", "name_en": "FTSE 100", "type": "index", "country_fa": "انگلیس", "country_en": "UK"},
        "DAX": {"name_fa": "داکس", "name_en": "DAX", "type": "index", "country_fa": "آلمان", "country_en": "Germany"},
        "NKY": {"name_fa": "نیکی", "name_en": "Nikkei 225", "type": "index", "country_fa": "ژاپن", "country_en": "Japan"},
        # Cryptocurrencies
        "BTC": {"name_fa": "بیت‌کوین", "name_en": "Bitcoin", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "ETH": {"name_fa": "اتریوم", "name_en": "Ethereum", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "BNB": {"name_fa": "بایننس کوین", "name_en": "Binance Coin", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "XRP": {"name_fa": "ریپل", "name_en": "Ripple", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "SOL": {"name_fa": "سولانا", "name_en": "Solana", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "ADA": {"name_fa": "کاردانو", "name_en": "Cardano", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "DOGE": {"name_fa": "دوج‌کوین", "name_en": "Dogecoin", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"},
        "DOT": {"name_fa": "پولکادات", "name_en": "Polkadot", "type": "crypto", "country_fa": "جهانی", "country_en": "Global"}
    }

    async def generate_daily_summary(self, articles: List[NewsArticle], timeframe: str = "H1", asset: str = "USD", lang: str = "fa") -> str:
        """Generate a daily market summary with asset trend analysis in any language"""
        articles_text = self._format_articles(articles[:15])
        
        # Get asset info based on language
        asset_data = self.ASSET_INFO.get(asset, {
            "name_fa": asset, "name_en": asset, "type": "unknown", 
            "country_fa": "نامشخص", "country_en": "Unknown"
        })
        
        # Use English name as fallback for all languages
        asset_name = asset_data.get(f'name_{lang}', asset_data.get('name_en', asset))
        country = asset_data.get(f'country_{lang}', asset_data.get('country_en', 'Unknown'))
        
        # Complete prompts in each language
        lang_prompts = {
            'en': {
                'system': "You are an expert financial market analyst. Provide comprehensive market analysis in English.",
                'sections': ['Market Summary', 'Economic Analysis', 'Political Analysis', 'Financial Markets', 'Key Headlines', 'Upcoming Events', 'Market Sentiment']
            },
            'fa': {
                'system': "شما یک تحلیلگر حرفه‌ای بازارهای مالی هستید. تحلیل جامع بازار را به زبان فارسی ارائه دهید.",
                'sections': ['خلاصه بازار', 'تحلیل اقتصادی', 'تحلیل سیاسی', 'وضعیت بازارهای مالی', 'تیترهای مهم', 'رویدادهای پیش رو', 'حال و هوای بازار']
            },
            'ar': {
                'system': "أنت محلل خبير في الأسواق المالية. قدم تحليلاً شاملاً للسوق باللغة العربية.",
                'sections': ['ملخص السوق', 'التحليل الاقتصادي', 'التحليل السياسي', 'حالة الأسواق المالية', 'العناوين الرئيسية', 'الأحداث القادمة', 'معنويات السوق']
            },
            'tr': {
                'system': "Uzman bir finansal piyasa analistisiniz. Kapsamlı piyasa analizini Türkçe olarak sunun.",
                'sections': ['Piyasa Özeti', 'Ekonomik Analiz', 'Politik Analiz', 'Finansal Piyasalar', 'Önemli Başlıklar', 'Yaklaşan Olaylar', 'Piyasa Duyarlılığı']
            },
            'de': {
                'system': "Sie sind ein erfahrener Finanzmarktanalyst. Erstellen Sie eine umfassende Marktanalyse auf Deutsch.",
                'sections': ['Marktübersicht', 'Wirtschaftsanalyse', 'Politische Analyse', 'Finanzmärkte', 'Wichtige Schlagzeilen', 'Kommende Ereignisse', 'Marktstimmung']
            },
            'fr': {
                'system': "Vous êtes un analyste expert des marchés financiers. Fournissez une analyse complète du marché en français.",
                'sections': ['Résumé du marché', 'Analyse économique', 'Analyse politique', 'Marchés financiers', 'Titres importants', 'Événements à venir', 'Sentiment du marché']
            },
            'es': {
                'system': "Eres un analista experto en mercados financieros. Proporciona un análisis completo del mercado en español.",
                'sections': ['Resumen del mercado', 'Análisis económico', 'Análisis político', 'Mercados financieros', 'Titulares importantes', 'Próximos eventos', 'Sentimiento del mercado']
            },
            'ru': {
                'system': "Вы эксперт-аналитик финансовых рынков. Предоставьте комплексный анализ рынка на русском языке.",
                'sections': ['Обзор рынка', 'Экономический анализ', 'Политический анализ', 'Финансовые рынки', 'Ключевые заголовки', 'Предстоящие события', 'Настроение рынка']
            },
            'zh': {
                'system': "您是一位专业的金融市场分析师。请用中文提供全面的市场分析。",
                'sections': ['市场概述', '经济分析', '政治分析', '金融市场', '重要头条', '即将发生的事件', '市场情绪']
            },
            'ja': {
                'system': "あなたは金融市場の専門アナリストです。日本語で包括的な市場分析を提供してください。",
                'sections': ['市場概要', '経済分析', '政治分析', '金融市場', '重要なヘッドライン', '今後のイベント', '市場センチメント']
            },
            'ko': {
                'system': "당신은 금융 시장 전문 분석가입니다. 한국어로 포괄적인 시장 분석을 제공하세요.",
                'sections': ['시장 개요', '경제 분석', '정치 분석', '금융 시장', '주요 헤드라인', '다가오는 이벤트', '시장 심리']
            },
            'pt': {
                'system': "Você é um analista especialista em mercados financeiros. Forneça uma análise abrangente do mercado em português.",
                'sections': ['Resumo do mercado', 'Análise econômica', 'Análise política', 'Mercados financeiros', 'Manchetes importantes', 'Próximos eventos', 'Sentimento do mercado']
            },
            'it': {
                'system': "Sei un analista esperto dei mercati finanziari. Fornisci un'analisi completa del mercato in italiano.",
                'sections': ['Riepilogo del mercato', 'Analisi economica', 'Analisi politica', 'Mercati finanziari', 'Titoli importanti', 'Prossimi eventi', 'Sentiment del mercato']
            },
            'hi': {
                'system': "आप एक विशेषज्ञ वित्तीय बाजार विश्लेषक हैं। हिंदी में व्यापक बाजार विश्लेषण प्रदान करें।",
                'sections': ['बाजार सारांश', 'आर्थिक विश्लेषण', 'राजनीतिक विश्लेषण', 'वित्तीय बाजार', 'महत्वपूर्ण सुर्खियां', 'आगामी घटनाएं', 'बाजार भावना']
            }
        }
        
        lang_data = lang_prompts.get(lang, lang_prompts['en'])
        sections = lang_data['sections']
        system_msg = lang_data['system']
        
        # Language names for explicit instruction
        lang_names = {
            'en': 'English', 'fa': 'Persian/Farsi', 'ar': 'Arabic', 'tr': 'Turkish',
            'de': 'German', 'fr': 'French', 'es': 'Spanish', 'ru': 'Russian',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'pt': 'Portuguese',
            'it': 'Italian', 'hi': 'Hindi'
        }
        target_lang_name = lang_names.get(lang, 'English')
        
        # Timeframe descriptions
        tf_desc = {
            "short": "Short-term", "medium": "Medium-term", "long": "Long-term",
            "M15": "Short-term", "H1": "Short-term", "H4": "Medium-term", "D1": "Long-term"
        }
        tf_name = tf_desc.get(timeframe, timeframe)
        
        # Build prompt with sections in target language - MORE EXPLICIT
        prompt = f"""Analyze the following news articles and provide a comprehensive market analysis.

IMPORTANT: You MUST write your ENTIRE response in {target_lang_name} language. Do NOT use any other language.

## News Articles:
{articles_text}

## Analysis Parameters:
- Asset: {asset_name} ({asset})
- Type: {asset_data['type']}
- Region: {country}
- Timeframe: {tf_name}

Please provide your analysis using these section headers (write content in {target_lang_name}):

**{sections[0]}**: [Provide market summary in {target_lang_name}]
**{sections[1]}**: [Provide economic analysis in {target_lang_name}]
**{sections[2]}**: [Provide political analysis in {target_lang_name}]
**{sections[3]}**: [Provide financial markets status in {target_lang_name}]
**{sections[4]}**: [List key headlines in {target_lang_name}]
**{sections[5]}**: [List upcoming events in {target_lang_name}]
**{sections[6]}**: [Describe market sentiment in {target_lang_name}]

Remember: Write EVERYTHING in {target_lang_name}. This is mandatory."""

        # Enhanced system message with explicit language instruction
        enhanced_system_msg = f"""{system_msg}

CRITICAL INSTRUCTION: You MUST respond ONLY in {target_lang_name} language. 
Every word of your response must be in {target_lang_name}.
Do not use English or any other language unless it's a proper noun or technical term.
If you cannot write in {target_lang_name}, translate your response to {target_lang_name}."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language using AI"""
        
        # Language names for translation
        lang_names = {
            'en': 'English', 'fa': 'Persian/Farsi', 'ar': 'Arabic', 'tr': 'Turkish',
            'de': 'German', 'fr': 'French', 'es': 'Spanish', 'ru': 'Russian',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'pt': 'Portuguese',
            'it': 'Italian', 'hi': 'Hindi'
        }
        target_lang_name = lang_names.get(target_lang, 'English')
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a professional translator. Translate the given text to {target_lang_name}. "
                                   f"Preserve all formatting, markdown, and structure. Only output the translated text, nothing else."
                    },
                    {
                        "role": "user", 
                        "content": f"Translate the following text to {target_lang_name}:\n\n{text}"
                    }
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return text  # Return original text if translation fails
    
    async def classify_article_pairs(self, article: NewsArticle, available_pairs: List[str]) -> List[str]:
        """Use LLM to classify which pairs an article is relevant to"""
        prompt = PAIR_CLASSIFIER_PROMPT.format(
            title=article.title,
            content=article.content[:500],
            pairs=", ".join(available_pairs)
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a forex news classifier. Respond only with a JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            result = self._extract_json(response.choices[0].message.content)
            if isinstance(result, list):
                return [p for p in result if p in available_pairs]
            return []
            
        except Exception as e:
            logger.error(f"Error classifying article: {e}")
            return []
    
    def _format_articles(self, articles: List[NewsArticle]) -> str:
        """Format articles for prompt"""
        formatted = []
        for i, article in enumerate(articles, 1):
            formatted.append(f"""
### Article {i}
**Source**: {article.source}
**Title**: {article.title}
**Content**: {article.content[:500]}...
**Importance**: {article.importance}
""")
        return "\n".join(formatted)
    
    def _parse_analysis(self, pair: str, text: str, sources_count: int) -> MarketAnalysis:
        """Parse analysis text into structured format"""
        # Simple parsing - extract key information
        sentiment = "Neutral"
        confidence = 50
        
        text_lower = text.lower()
        if "bullish" in text_lower:
            sentiment = "Bullish"
            confidence = 70
        elif "bearish" in text_lower:
            sentiment = "Bearish"
            confidence = 70
        
        # Extract key factors (simple extraction)
        key_factors = []
        if "interest rate" in text_lower or "rate" in text_lower:
            key_factors.append("Interest rate expectations")
        if "inflation" in text_lower:
            key_factors.append("Inflation data")
        if "employment" in text_lower or "jobs" in text_lower:
            key_factors.append("Employment data")
        if "gdp" in text_lower:
            key_factors.append("GDP growth")
        
        return MarketAnalysis(
            pair=pair,
            sentiment=sentiment,
            confidence=confidence,
            summary=text,
            key_factors=key_factors if key_factors else ["General market conditions"],
            technical_outlook="See analysis above",
            risk_factors=["Market volatility", "Unexpected news events"],
            sources_count=sources_count
        )
    
    def _extract_json(self, text: str) -> Optional[Any]:
        """Extract JSON from text response"""
        import re
        
        # Try to find JSON in the response
        json_patterns = [
            r'\{[\s\S]*\}',  # Object
            r'\[[\s\S]*\]'   # Array
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Try parsing the whole text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def analyze_multi_timeframe(
        self, 
        pair: str, 
        primary_tf: str,
        articles: List[NewsArticle],
        trading_style: str = "day_trading",
        timeframes: List[str] = None
    ) -> MultiTimeframeAnalysis:
        """
        Perform comprehensive multi-timeframe analysis
        
        Args:
            pair: Currency pair
            primary_tf: Primary timeframe for trading
            articles: News articles for context
            trading_style: scalping, day_trading, swing_trading, position_trading
            timeframes: Optional list of specific timeframes to analyze
        """
        # Map trading style names
        style_map = {
            'scalping': 'scalp', 'scalp': 'scalp',
            'day_trading': 'day', 'day': 'day',
            'swing_trading': 'swing', 'swing': 'swing',
            'position_trading': 'position', 'position': 'position'
        }
        normalized_style = style_map.get(trading_style, 'day')
        style_config = self.TRADING_STYLES.get(normalized_style, self.TRADING_STYLES['day'])
        
        # Get timeframes to analyze - use provided list or get from config
        if timeframes and len(timeframes) > 1:
            tf_list = timeframes
        else:
            tf_list = get_mtf_timeframes(primary_tf)
        
        # Prepare news context
        relevant_articles = [a for a in articles if pair in a.currency_pairs or not a.currency_pairs]
        news_context = self._format_articles(relevant_articles[:10])
        
        # Get style parameters
        style_params = self._get_style_params(normalized_style)
        
        prompt = MULTI_TIMEFRAME_PROMPT.format(
            pair=pair,
            trading_style=style_config['name'],
            timeframes=", ".join(tf_list),
            primary_tf=primary_tf,
            news_context=news_context
        )
        
        system_prompt = f"""You are an expert multi-timeframe forex analyst specializing in {style_config['name']}.
Analyze ALL provided timeframes: {', '.join(tf_list)}
Primary entry timeframe: {primary_tf}

Trading Style Parameters:
{style_params}

You MUST respond with valid JSON only. Provide specific price levels and actionable recommendations.
Grade the setup quality honestly based on timeframe alignment and confluence."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=3000
            )
            
            result = self._extract_json(response.choices[0].message.content)
            
            if result:
                # Parse timeframe details
                tf_details = {}
                for tf, data in result.get("timeframe_analysis", {}).items():
                    tf_details[tf] = TimeframeAnalysis(
                        timeframe=tf,
                        trend=data.get("trend", "neutral"),
                        strength=data.get("strength", "moderate"),
                        support_levels=data.get("support", []),
                        resistance_levels=data.get("resistance", []),
                        momentum=data.get("momentum", "flat"),
                        bias_score=data.get("bias_score", 50)
                    )
                
                confluence = result.get("confluence", {})
                
                return MultiTimeframeAnalysis(
                    pair=pair,
                    primary_timeframe=primary_tf,
                    timeframes_analyzed=tf_list,
                    timeframe_details=tf_details,
                    confluence=confluence,
                    overall_bias=confluence.get("overall_bias", "neutral"),
                    confidence=confluence.get("confidence", 50),
                    trade_recommendation=result.get("trade_recommendation", {})
                )
            else:
                raise ValueError("Could not parse MTF analysis")
                
        except Exception as e:
            logger.error(f"Error in MTF analysis for {pair}: {e}")
            return MultiTimeframeAnalysis(
                pair=pair,
                primary_timeframe=primary_tf,
                timeframes_analyzed=tf_list,
                timeframe_details={},
                confluence={"error": str(e)},
                overall_bias="neutral",
                confidence=0,
                trade_recommendation={"action": "WAIT", "reason": "Analysis failed"}
            )

    async def analyze_specific_timeframe(
        self,
        pair: str,
        timeframe: str,
        articles: List[NewsArticle],
        trading_style: str = "day_trading",
        risk_profile: str = "moderate"
    ) -> Dict:
        """
        Analyze pair for a specific timeframe with comprehensive details
        
        Args:
            pair: Currency pair
            timeframe: Specific timeframe (M15, H1, H4, etc.)
            articles: News articles
            trading_style: Trading style
            risk_profile: conservative, moderate, aggressive
        """
        # Map trading style
        style_map = {
            'scalping': 'scalp', 'scalp': 'scalp',
            'day_trading': 'day', 'day': 'day',
            'swing_trading': 'swing', 'swing': 'swing',
            'position_trading': 'position', 'position': 'position'
        }
        normalized_style = style_map.get(trading_style, 'day')
        style_config = self.TRADING_STYLES.get(normalized_style, self.TRADING_STYLES['day'])
        
        relevant_articles = [a for a in articles if pair in a.currency_pairs or not a.currency_pairs]
        news_context = self._format_articles(relevant_articles[:8])
        
        # Get timeframe-specific guidelines
        tf_guidelines = TIMEFRAME_GUIDELINES.get(timeframe, TIMEFRAME_GUIDELINES.get('H1', ''))
        
        prompt = TIMEFRAME_SPECIFIC_PROMPT.format(
            pair=pair,
            timeframe=timeframe,
            news_context=news_context,
            trading_style=style_config['name'],
            risk_profile=risk_profile,
            timeframe_guidelines=tf_guidelines
        )
        
        system_prompt = f"""You are an expert forex analyst specializing in {timeframe} timeframe trading.
Trading Style: {style_config['name']}
Risk Profile: {risk_profile}

Timeframe Guidelines: {tf_guidelines}

You MUST respond with valid JSON only. Provide specific, actionable analysis with:
- Exact entry zones and triggers
- Precise SL/TP levels in pips
- Multiple take profit targets
- Clear trade management rules"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            result = self._extract_json(response.choices[0].message.content)
            return result if result else {"error": "Could not parse response"}
            
        except Exception as e:
            logger.error(f"Error analyzing {pair} for {timeframe}: {e}")
            return {"error": str(e)}

    def get_trading_styles(self) -> Dict:
        """Get available trading styles"""
        return TRADING_STYLES

    def get_timeframe_names(self) -> Dict:
        """Get timeframe display names"""
        return TIMEFRAME_NAMES
