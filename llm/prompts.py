"""
Prompt Templates for AI Analysis
"""

ANALYSIS_PROMPT = """You are an expert forex market analyst. Analyze the following news articles and provide a comprehensive market analysis.

## News Articles:
{articles}

## Currency Pair: {pair}
## Trading Style: {trading_style}
## Primary Timeframe: {timeframe}
## Analysis Timeframes: {timeframes}

Please provide a detailed analysis considering the trading style and timeframes:

1. **Market Sentiment Summary**: 
   - Overall sentiment (Bullish/Bearish/Neutral)
   - Confidence level (1-100%)
   - Sentiment strength for each timeframe

2. **Key Factors**:
   - Fundamental factors affecting this pair
   - Economic indicators impact
   - Central bank policy implications

3. **Technical Outlook**:
   - Key support levels (at least 3)
   - Key resistance levels (at least 3)
   - Trend direction on each timeframe
   - Important chart patterns

4. **Timeframe-Specific Analysis**:
   - Short-term outlook (for scalp/day trading)
   - Medium-term outlook (for swing trading)
   - Long-term outlook (for position trading)

5. **Risk Factors**:
   - Upcoming high-impact news events
   - Geopolitical risks
   - Market volatility assessment

6. **Trade Setup Quality**:
   - Rate the current setup (A+, A, B, C, D)
   - Best entry timing
   - Recommended position sizing

Respond in a structured format optimized for {trading_style} traders on {timeframe} timeframe.
"""

TRADE_SUGGESTION_PROMPT = """You are an expert forex trading advisor. Based on the following market analysis, provide a specific trade recommendation.

## Market Analysis:
{analysis}

## Currency Pair: {pair}
## Trading Style: {trading_style}
## Primary Timeframe: {timeframe}
## Analysis Timeframes: {timeframes}

## Pair Configuration:
- Volatility: {volatility}
- Base SL (pips): {default_sl}
- Base TP (pips): {default_tp}

## Trading Style Parameters:
{style_params}

IMPORTANT RULES:
1. You MUST provide a BUY or SELL recommendation. Only use WAIT if there is absolutely NO clear direction.
2. Adjust SL/TP based on the trading style:
   - Scalp: Tight SL (10-20 pips), Quick TP (15-30 pips), R:R 1:1.5+
   - Day Trading: Medium SL (20-40 pips), TP (40-80 pips), R:R 1:2+
   - Swing: Wide SL (50-100 pips), TP (100-200 pips), R:R 1:2+
   - Position: Very wide SL (100-200 pips), TP (200-500 pips), R:R 1:2.5+

3. Consider timeframe alignment:
   - Entry on lower timeframe
   - Confirmation on higher timeframe
   - Trend direction on highest timeframe

Provide your recommendation in this JSON format:
{{
    "recommendation": "BUY" | "SELL" | "WAIT",
    "confidence": 1-100,
    "timeframe": "{timeframe}",
    "trading_style": "{trading_style}",
    "entry_zone": {{
        "type": "market" | "limit" | "stop",
        "price_description": "specific entry zone description",
        "best_entry_time": "optimal session/time for entry"
    }},
    "stop_loss": {{
        "pips": <adjusted for trading style>,
        "description": "technical reason for SL placement",
        "level_type": "below support" | "above resistance" | "ATR-based"
    }},
    "take_profit": {{
        "pips": <adjusted for trading style>,
        "tp1_pips": <first target>,
        "tp2_pips": <second target>,
        "tp3_pips": <final target>,
        "description": "technical reason for TP placement"
    }},
    "risk_reward_ratio": <calculated R:R>,
    "position_size_recommendation": "1-2% risk" | "0.5-1% risk" | "2-3% risk",
    "trade_duration": "expected duration based on style",
    "reasoning": "detailed explanation including timeframe analysis",
    "key_levels": ["support1", "support2", "resistance1", "resistance2"],
    "invalidation": "specific price level or condition that invalidates the trade",
    "news_to_watch": ["specific upcoming events with dates/times"],
    "confluence_factors": ["list of factors supporting this trade"],
    "setup_grade": "A+" | "A" | "B" | "C"
}}

Guidelines:
- Prefer BUY or SELL over WAIT - traders want actionable signals
- Adjust SL/TP based on trading style (scalp=tight, position=wide)
- Minimum R:R ratio: 1:1.5 for scalp, 1:2 for day/swing, 1:2.5 for position
- Consider volatility when setting levels
- Include multiple TP targets for partial profit taking
- Grade the setup quality honestly
"""

PAIR_CLASSIFIER_PROMPT = """Analyze the following news article and determine which currency pairs it is most relevant to.

Article Title: {title}
Article Content: {content}

Available pairs: {pairs}

Return a JSON array of relevant pairs, ordered by relevance. Example: ["EURUSD", "GBPUSD"]
If no pairs are clearly relevant, return an empty array: []
"""

SUMMARY_PROMPT_FA = """شما یک تحلیلگر حرفه‌ای بازار فارکس و اقتصاد جهانی هستید. اخبار زیر را تحلیل کنید.

اخبار:
{articles}

لطفاً موارد زیر را به زبان فارسی ارائه دهید:

## تحلیل کلی
1. **خلاصه بازار**: وضعیت کلی بازار در ۲-۳ جمله
2. **تحلیل اقتصادی**: وضعیت اقتصاد کشور مربوطه (نرخ بهره، تورم، اشتغال)
3. **تحلیل سیاسی**: تأثیر رویدادهای سیاسی بر بازار
4. **وضعیت بازارهای مالی**: وضعیت بورس‌ها و شاخص‌های مهم

## نکات کلیدی
- **تیترهای مهم**: نکات کلیدی به صورت لیست
- **رویدادهای پیش رو**: رویدادهای اقتصادی مهم آینده
- **حال و هوای بازار**: صعودی، نزولی یا خنثی

## پیش‌بینی
- جهت احتمالی حرکت در کوتاه مدت
- سطوح کلیدی حمایت و مقاومت

پاسخ را کاملاً به زبان فارسی بنویسید و مختصر و کاربردی باشد.
"""

SUMMARY_PROMPT_EN = """You are an expert forex and global economy analyst. Analyze the following news.

News:
{articles}

Please provide the following in English:

## General Analysis
1. **Market Summary**: Overall market conditions in 2-3 sentences
2. **Economic Analysis**: Economic situation of the relevant country (interest rates, inflation, employment)
3. **Political Analysis**: Impact of political events on the market
4. **Financial Markets Status**: Stock markets and major indices status

## Key Points
- **Important Headlines**: Key points as a list
- **Upcoming Events**: Important upcoming economic events
- **Market Sentiment**: Bullish, Bearish, or Neutral

## Forecast
- Probable direction of movement in the short term
- Key support and resistance levels

Provide a concise and actionable response in English.
"""

# For backward compatibility
SUMMARY_PROMPT = SUMMARY_PROMPT_FA

MULTI_TIMEFRAME_PROMPT = """You are an expert forex analyst performing comprehensive multi-timeframe analysis.

## Currency Pair: {pair}
## Trading Style: {trading_style}
## Timeframes to Analyze: {timeframes}
## Primary Timeframe (Entry): {primary_tf}

## Market News & Context:
{news_context}

## Multi-Timeframe Analysis Rules:
1. **Higher Timeframe (HTF)**: Determines overall trend direction
2. **Middle Timeframe (MTF)**: Confirms trend and identifies key levels
3. **Lower Timeframe (LTF)**: Provides precise entry timing

For EACH timeframe in {timeframes}, analyze:
1. **Trend Direction**: Bullish / Bearish / Neutral (with reasoning)
2. **Trend Strength**: Strong / Moderate / Weak (based on momentum)
3. **Key Support Levels**: At least 3 levels with descriptions
4. **Key Resistance Levels**: At least 3 levels with descriptions
5. **Momentum**: Increasing / Decreasing / Flat
6. **Bias Score**: 0-100 (0=strong bearish, 50=neutral, 100=strong bullish)
7. **Key Patterns**: Any chart patterns visible

Then provide **Multi-Timeframe Confluence Analysis**:
- Alignment score (how well do timeframes agree?)
- Conflicting signals (if any)
- Dominant trend direction
- Best entry scenario

Respond in this JSON format:
{{
    "timeframe_analysis": {{
        "<timeframe>": {{
            "trend": "bullish|bearish|neutral",
            "trend_reasoning": "why this trend",
            "strength": "strong|moderate|weak",
            "support": ["level1 - description", "level2 - description", "level3 - description"],
            "resistance": ["level1 - description", "level2 - description", "level3 - description"],
            "momentum": "increasing|decreasing|flat",
            "bias_score": 1-100,
            "key_patterns": ["pattern1", "pattern2"],
            "notes": "additional observations"
        }}
    }},
    "confluence": {{
        "aligned": true|false,
        "alignment_score": 1-100,
        "overall_bias": "bullish|bearish|neutral",
        "bias_strength": "strong|moderate|weak",
        "confidence": 1-100,
        "conflicting_signals": ["list any conflicts"],
        "best_entry_tf": "timeframe",
        "best_confirmation_tf": "timeframe",
        "trend_tf": "timeframe for trend direction",
        "summary": "detailed explanation of MTF analysis"
    }},
    "trade_recommendation": {{
        "action": "BUY|SELL|WAIT",
        "confidence": 1-100,
        "entry_tf": "timeframe for entry",
        "entry_type": "market|limit|stop",
        "entry_zone": "description of entry area",
        "confirmation_tf": "timeframe for confirmation",
        "confirmation_signal": "what to look for",
        "sl_pips": <number>,
        "tp_pips": <number>,
        "tp1_pips": <first target>,
        "tp2_pips": <second target>,
        "risk_reward": <ratio>,
        "invalidation": "specific condition that invalidates setup",
        "trade_duration": "expected duration",
        "setup_grade": "A+|A|B|C|D"
    }}
}}

IMPORTANT:
- Analyze ALL provided timeframes, not just the primary one
- Be specific with support/resistance levels
- Provide actionable trade recommendations
- Grade the setup honestly based on confluence
"""

TIMEFRAME_SPECIFIC_PROMPT = """Analyze {pair} specifically for {timeframe} timeframe trading.

## News Context:
{news_context}

## Trading Parameters:
- Trading Style: {trading_style}
- Risk Profile: {risk_profile}
- Timeframe: {timeframe}

## Timeframe-Specific Guidelines:
{timeframe_guidelines}

Provide a comprehensive analysis for {timeframe} traders:

1. **Market Bias**: Current directional bias with confidence
2. **Entry Strategy**: 
   - Optimal entry zones
   - Entry triggers to watch
   - Best entry timing (session)
3. **Risk Management**:
   - Stop loss placement (in pips and reasoning)
   - Take profit targets (multiple levels)
   - Position sizing recommendation
4. **Trade Management**:
   - When to move SL to breakeven
   - Partial profit taking levels
   - Trail stop strategy
5. **Timing**:
   - Best trading sessions
   - Times to avoid
   - Upcoming news events

Respond in JSON:
{{
    "timeframe": "{timeframe}",
    "trading_style": "{trading_style}",
    "analysis": {{
        "bias": "bullish|bearish|neutral",
        "bias_strength": "strong|moderate|weak",
        "confidence": 1-100,
        "entry_zone": {{
            "description": "detailed entry zone",
            "entry_trigger": "what signal to wait for",
            "entry_type": "market|limit|stop"
        }},
        "sl_pips": <number>,
        "sl_reasoning": "why this SL level",
        "tp1_pips": <first target>,
        "tp2_pips": <second target>,
        "tp3_pips": <final target>,
        "tp_reasoning": "why these TP levels",
        "risk_reward": <ratio>,
        "position_size": "% of account to risk",
        "expected_duration": "hours/days",
        "best_session": "London|NewYork|Asian|Overlap",
        "avoid_times": ["specific times/events to avoid"],
        "breakeven_trigger": "when to move SL to BE",
        "trail_strategy": "how to trail stop"
    }},
    "key_levels": {{
        "support": ["level1", "level2", "level3"],
        "resistance": ["level1", "level2", "level3"],
        "pivot_points": ["daily pivot", "weekly pivot"]
    }},
    "upcoming_events": [
        {{"event": "name", "time": "datetime", "impact": "high|medium|low"}}
    ],
    "reasoning": "detailed explanation of the analysis",
    "setup_grade": "A+|A|B|C|D",
    "warnings": ["any cautions or warnings"]
}}
"""

# Timeframe-specific guidelines
TIMEFRAME_GUIDELINES = {
    'M1': 'Ultra short-term scalping. SL: 5-10 pips, TP: 5-15 pips. Duration: seconds to minutes.',
    'M5': 'Short-term scalping. SL: 10-15 pips, TP: 15-25 pips. Duration: minutes.',
    'M15': 'Scalp to day trading. SL: 15-25 pips, TP: 25-50 pips. Duration: minutes to hours.',
    'M30': 'Day trading. SL: 20-35 pips, TP: 40-70 pips. Duration: hours.',
    'H1': 'Day trading. SL: 30-50 pips, TP: 60-100 pips. Duration: hours to 1 day.',
    'H4': 'Swing trading. SL: 50-80 pips, TP: 100-160 pips. Duration: days.',
    'D1': 'Swing to position. SL: 80-150 pips, TP: 150-300 pips. Duration: days to weeks.',
    'W1': 'Position trading. SL: 150-300 pips, TP: 300-600 pips. Duration: weeks to months.',
    'MN1': 'Long-term position. SL: 300-500 pips, TP: 500-1000 pips. Duration: months.'
}
