"""
Chart Image Analyzer - AI-powered chart analysis using OpenAI Vision
"""
import base64
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from datetime import datetime

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL, PAIR_CONFIGS

logger = logging.getLogger(__name__)


class ChartImageAnalyzer:
    """Analyze forex charts using OpenAI Vision API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.vision_model = "gpt-4o"  # GPT-4 Vision model
    
    async def analyze_chart_image(
        self,
        pair: str,
        image_data: str,  # base64 encoded image
        timeframe: str = "H1",
        trading_style: str = "day"
    ) -> Dict[str, Any]:
        """
        Analyze a chart image and provide trade recommendation
        
        Args:
            pair: Currency pair (e.g., EURUSD)
            image_data: Base64 encoded chart image
            timeframe: Trading timeframe
            trading_style: Trading style (scalp, day, swing, position)
        
        Returns:
            Dictionary with analysis and trade recommendation
        """
        try:
            pair_config = PAIR_CONFIGS.get(pair, {
                "volatility": "medium",
                "default_sl_pips": 30,
                "default_tp_pips": 60
            })
            
            # Create detailed prompt for chart analysis
            prompt = f"""You are an expert forex trader analyzing a {pair} chart on {timeframe} timeframe for {trading_style} trading.

Analyze this chart image carefully and provide:

1. **Market Structure**: Identify current trend, support/resistance levels, chart patterns
2. **Technical Analysis**: Key indicators, price action signals, momentum
3. **Trade Setup**: Specific entry zone, stop loss, and take profit levels
4. **Risk Management**: Risk-reward ratio and position sizing

Provide your analysis in this EXACT JSON format:
{{
    "sentiment": "Bullish|Bearish|Neutral",
    "confidence": 0-100,
    "trend": "uptrend|downtrend|sideways",
    "key_levels": {{
        "support": ["level1", "level2"],
        "resistance": ["level1", "level2"]
    }},
    "recommendation": {{
        "action": "BUY|SELL|WAIT",
        "entry_zone": {{
            "min": "price",
            "max": "price",
            "description": "entry description"
        }},
        "stop_loss": {{
            "price": "SL price",
            "pips": number,
            "description": "SL reasoning"
        }},
        "take_profit": {{
            "price": "TP price",
            "pips": number,
            "description": "TP reasoning"
        }},
        "risk_reward_ratio": number,
        "confidence": 0-100
    }},
    "reasoning": "Detailed explanation of the trade setup",
    "key_factors": ["factor1", "factor2", "factor3"],
    "invalidation": "What would invalidate this setup",
    "timeframe_alignment": "How this aligns with higher/lower timeframes"
}}

Pair Configuration:
- Volatility: {pair_config.get('volatility', 'medium')}
- Typical SL: {pair_config.get('default_sl_pips', 30)} pips
- Typical TP: {pair_config.get('default_tp_pips', 60)} pips

Be specific with price levels and provide actionable trade recommendations."""

            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert forex trader specializing in {trading_style} trading on {timeframe} timeframe. Provide precise, actionable trade setups with specific entry, SL, and TP levels."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON in response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                analysis_data = self._parse_text_response(analysis_text, pair)
            
            # Format response
            return {
                'pair': pair,
                'timeframe': timeframe,
                'trading_style': trading_style,
                'analysis': {
                    'sentiment': analysis_data.get('sentiment', 'Neutral'),
                    'sentiment_score': analysis_data.get('confidence', 50),
                    'trend': analysis_data.get('trend', 'sideways'),
                    'key_factors': analysis_data.get('key_factors', []),
                    'support_levels': analysis_data.get('key_levels', {}).get('support', []),
                    'resistance_levels': analysis_data.get('key_levels', {}).get('resistance', []),
                    'summary': analysis_data.get('reasoning', 'Chart analysis completed'),
                },
                'recommendation': {
                    'recommendation': analysis_data.get('recommendation', {}).get('action', 'WAIT'),
                    'confidence': analysis_data.get('recommendation', {}).get('confidence', 0),
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                    'entry_zone': analysis_data.get('recommendation', {}).get('entry_zone', {}),
                    'stop_loss': analysis_data.get('recommendation', {}).get('stop_loss', {}),
                    'take_profit': analysis_data.get('recommendation', {}).get('take_profit', {}),
                    'risk_reward_ratio': analysis_data.get('recommendation', {}).get('risk_reward_ratio', 0),
                    'reasoning': analysis_data.get('reasoning', ''),
                    'key_levels': [
                        *analysis_data.get('key_levels', {}).get('support', []),
                        *analysis_data.get('key_levels', {}).get('resistance', [])
                    ],
                    'invalidation': analysis_data.get('invalidation', ''),
                },
                'generated_at': datetime.now().isoformat(),
                'source': 'chart_image_analysis'
            }
            
        except Exception as e:
            logger.error(f"Chart image analysis error for {pair}: {e}", exc_info=True)
            return {
                'pair': pair,
                'error': str(e),
                'analysis': {
                    'sentiment': 'Unknown',
                    'sentiment_score': 0,
                    'key_factors': [f'خطا در تحلیل تصویر: {str(e)}'],
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
                'generated_at': datetime.now().isoformat()
            }
    
    async def analyze_multi_timeframe_charts(
        self,
        pair: str,
        chart_images: Dict[str, str],  # {timeframe: base64_image_data}
        trading_style: str = "day"
    ) -> Dict[str, Any]:
        """
        Analyze multiple timeframe charts for comprehensive trade setup
        
        Args:
            pair: Currency pair (e.g., EURUSD)
            chart_images: Dictionary of timeframe to base64 encoded images
            trading_style: Trading style (scalp, day, swing, position)
        
        Returns:
            Dictionary with multi-timeframe analysis and trade recommendation
        """
        try:
            pair_config = PAIR_CONFIGS.get(pair, {
                "volatility": "medium",
                "default_sl_pips": 30,
                "default_tp_pips": 60
            })
            
            # Build timeframe list for prompt
            timeframe_list = ", ".join(chart_images.keys())
            
            # Create detailed prompt for multi-timeframe analysis
            prompt = f"""You are an expert forex trader analyzing {pair} across MULTIPLE TIMEFRAMES: {timeframe_list} for {trading_style} trading.

I'm providing you with {len(chart_images)} chart images showing different timeframes. Analyze ALL charts together to:

1. **Multi-Timeframe Alignment**: Check if trends align across timeframes
2. **Higher Timeframe Context**: Identify major support/resistance and trend direction
3. **Lower Timeframe Entry**: Find precise entry points on lower timeframes
4. **Confluence Zones**: Areas where multiple timeframes show the same signal

Provide your analysis in this EXACT JSON format:
{{
    "sentiment": "Bullish|Bearish|Neutral",
    "confidence": 0-100,
    "trend": "uptrend|downtrend|sideways",
    "timeframe_analysis": {{
        "{list(chart_images.keys())[0] if chart_images else 'H1'}": "analysis of this timeframe",
        "{list(chart_images.keys())[1] if len(chart_images) > 1 else 'H4'}": "analysis of this timeframe"
    }},
    "alignment": "aligned|conflicting|neutral",
    "key_levels": {{
        "support": ["level1", "level2"],
        "resistance": ["level1", "level2"]
    }},
    "recommendation": {{
        "action": "BUY|SELL|WAIT",
        "entry_zone": {{
            "min": "price",
            "max": "price",
            "description": "entry description with timeframe context"
        }},
        "stop_loss": {{
            "price": "SL price",
            "pips": number,
            "description": "SL reasoning based on higher timeframe"
        }},
        "take_profit": {{
            "price": "TP price",
            "pips": number,
            "description": "TP reasoning based on higher timeframe targets"
        }},
        "risk_reward_ratio": number,
        "confidence": 0-100
    }},
    "reasoning": "Detailed explanation of multi-timeframe setup",
    "key_factors": ["factor1", "factor2", "factor3"],
    "invalidation": "What would invalidate this setup",
    "timeframe_confluence": "How timeframes support each other"
}}

Pair Configuration:
- Volatility: {pair_config.get('volatility', 'medium')}
- Typical SL: {pair_config.get('default_sl_pips', 30)} pips
- Typical TP: {pair_config.get('default_tp_pips', 60)} pips

Be specific with price levels and explain how each timeframe contributes to the trade setup."""

            # Build message content with all chart images
            message_content = [{"type": "text", "text": prompt}]
            
            for timeframe, image_data in chart_images.items():
                if image_data:  # Only add if image exists
                    message_content.append({
                        "type": "text",
                        "text": f"\n--- Chart for {timeframe} timeframe ---"
                    })
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    })
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert forex trader specializing in multi-timeframe analysis for {trading_style} trading. Provide precise, actionable trade setups based on timeframe confluence."
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                max_tokens=2500,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                analysis_data = self._parse_text_response(analysis_text, pair)
            
            # Format response
            return {
                'pair': pair,
                'timeframes': list(chart_images.keys()),
                'trading_style': trading_style,
                'analysis': {
                    'sentiment': analysis_data.get('sentiment', 'Neutral'),
                    'sentiment_score': analysis_data.get('confidence', 50),
                    'trend': analysis_data.get('trend', 'sideways'),
                    'alignment': analysis_data.get('alignment', 'neutral'),
                    'timeframe_analysis': analysis_data.get('timeframe_analysis', {}),
                    'key_factors': analysis_data.get('key_factors', []),
                    'support_levels': analysis_data.get('key_levels', {}).get('support', []),
                    'resistance_levels': analysis_data.get('key_levels', {}).get('resistance', []),
                    'summary': analysis_data.get('reasoning', 'Multi-timeframe analysis completed'),
                    'timeframe_confluence': analysis_data.get('timeframe_confluence', ''),
                },
                'recommendation': {
                    'recommendation': analysis_data.get('recommendation', {}).get('action', 'WAIT'),
                    'confidence': analysis_data.get('recommendation', {}).get('confidence', 0),
                    'timeframes': list(chart_images.keys()),
                    'trading_style': trading_style,
                    'entry_zone': analysis_data.get('recommendation', {}).get('entry_zone', {}),
                    'stop_loss': analysis_data.get('recommendation', {}).get('stop_loss', {}),
                    'take_profit': analysis_data.get('recommendation', {}).get('take_profit', {}),
                    'risk_reward_ratio': analysis_data.get('recommendation', {}).get('risk_reward_ratio', 0),
                    'reasoning': analysis_data.get('reasoning', ''),
                    'key_levels': [
                        *analysis_data.get('key_levels', {}).get('support', []),
                        *analysis_data.get('key_levels', {}).get('resistance', [])
                    ],
                    'invalidation': analysis_data.get('invalidation', ''),
                },
                'generated_at': datetime.now().isoformat(),
                'source': 'multi_timeframe_chart_analysis'
            }
            
        except Exception as e:
            logger.error(f"Multi-timeframe chart analysis error for {pair}: {e}", exc_info=True)
            return {
                'pair': pair,
                'error': str(e),
                'analysis': {
                    'sentiment': 'Unknown',
                    'sentiment_score': 0,
                    'key_factors': [f'خطا در تحلیل چند تایم‌فریم: {str(e)}'],
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 0,
                    'timeframes': list(chart_images.keys()) if chart_images else [],
                    'trading_style': trading_style,
                    'reasoning': f'خطا در تحلیل: {str(e)}',
                    'stop_loss': {'pips': 0, 'description': 'خطا'},
                    'take_profit': {'pips': 0, 'description': 'خطا'}
                },
                'generated_at': datetime.now().isoformat()
            }
    
    def _parse_text_response(self, text: str, pair: str) -> Dict:
        """Fallback parser for non-JSON responses"""
        return {
            'sentiment': 'Neutral',
            'confidence': 50,
            'trend': 'sideways',
            'key_factors': ['تحلیل متنی دریافت شد'],
            'reasoning': text[:500],
            'recommendation': {
                'action': 'WAIT',
                'confidence': 0,
                'entry_zone': {},
                'stop_loss': {'pips': 0, 'description': 'نیاز به بررسی دستی'},
                'take_profit': {'pips': 0, 'description': 'نیاز به بررسی دستی'},
                'risk_reward_ratio': 0
            }
        }
