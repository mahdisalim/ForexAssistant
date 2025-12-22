"""
Views for Analysis App
AI-powered forex analysis with real-time LLM integration and chart image analysis
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CurrencyPair, MarketAnalysis

logger = logging.getLogger(__name__)


def get_pairs_config():
    """Load pairs configuration from file or database"""
    pairs_file = settings.DATA_DIR / "pairs.json"
    if pairs_file.exists():
        with open(pairs_file, "r") as f:
            return json.load(f)
    return {pair: settings.PAIR_CONFIGS.get(pair, {}) for pair in settings.DEFAULT_PAIRS}


def save_pairs_config(pairs):
    """Save pairs configuration to file"""
    pairs_file = settings.DATA_DIR / "pairs.json"
    with open(pairs_file, "w") as f:
        json.dump(pairs, f, indent=2)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_pairs(request):
    """List all configured currency pairs"""
    return Response({'pairs': get_pairs_config()})


@api_view(['POST'])
@permission_classes([AllowAny])
def add_pair(request):
    """Add a new currency pair"""
    pairs = get_pairs_config()
    
    pair = request.data.get('pair', '').upper().replace('/', '')
    if len(pair) != 6:
        return Response(
            {'detail': 'Invalid pair format. Use format like EURUSD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if pair in pairs:
        return Response(
            {'detail': f'Pair {pair} already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    config = request.data.get('config', {
        'volatility': 'medium',
        'default_sl_pips': 30,
        'default_tp_pips': 60,
        'keywords': [pair[:3], pair[3:]]
    })
    
    pairs[pair] = config
    save_pairs_config(pairs)
    
    return Response({
        'message': f'Pair {pair} added successfully',
        'pair': pair,
        'config': config
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_pair(request, pair):
    """Remove a currency pair"""
    pairs = get_pairs_config()
    pair = pair.upper()
    
    if pair not in pairs:
        return Response(
            {'detail': f'Pair {pair} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    del pairs[pair]
    save_pairs_config(pairs)
    
    return Response({'message': f'Pair {pair} removed successfully'})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_analysis(request, pair):
    """
    Get AI analysis for a currency pair - automatically captures chart and analyzes
    """
    pair = pair.upper()
    pairs = get_pairs_config()
    
    if pair not in pairs:
        return Response(
            {'detail': f'Pair {pair} not configured'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    timeframe = request.query_params.get('timeframe', 'H1')
    trading_style = request.query_params.get('trading_style', 'day')
    
    # Get analysis service and trigger automatic chart analysis
    from .services import get_analysis_service
    import asyncio
    
    try:
        service = get_analysis_service()
        
        # Run async analysis in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Use analyze_chart_auto for automatic chart capture and analysis
            result = loop.run_until_complete(
                service.analyze_chart_auto(pair, timeframe, trading_style)
            )
        finally:
            loop.close()
        
        if result:
            return Response(result)
        else:
            return Response({
                'pair': pair,
                'analysis': {
                    'sentiment': 'Neutral',
                    'sentiment_score': 50,
                    'key_factors': ['در حال دریافت تحلیل'],
                },
                'recommendation': {
                    'recommendation': 'WAIT',
                    'confidence': 0,
                    'timeframe': timeframe,
                    'trading_style': trading_style,
                },
                'generated_at': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Analysis error for {pair}: {str(e)}")
        return Response({
            'pair': pair,
            'error': str(e),
            'analysis': {
                'sentiment': 'Neutral',
                'sentiment_score': 50,
                'key_factors': [f'خطا: {str(e)}'],
            },
            'recommendation': {
                'recommendation': 'WAIT',
                'confidence': 0,
                'timeframe': timeframe,
                'trading_style': trading_style,
            },
            'generated_at': datetime.now().isoformat()
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_analysis(request):
    """Get analysis for all configured pairs"""
    pairs = get_pairs_config()
    timeframe = request.query_params.get('timeframe', 'H1')
    trading_style = request.query_params.get('trading_style', 'day')
    
    # TODO: PRIORITY_NEXT - Implement full analysis for all pairs
    results = []
    for pair in pairs.keys():
        results.append({
            'pair': pair,
            'analysis': {'sentiment': 'neutral', 'note': 'Full AI analysis pending'},
            'recommendation': {'recommendation': 'WAIT', 'confidence': 0},
            'timeframe': timeframe,
            'trading_style': trading_style
        })
    
    return Response({
        'generated_at': datetime.now().isoformat(),
        'pairs_count': len(results),
        'timeframe': timeframe,
        'trading_style': trading_style,
        'results': results
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_summary(request):
    """Get daily market summary - scrapes 5 news sources and generates AI summary"""
    import asyncio
    from .services import get_analysis_service
    
    timeframe = request.query_params.get('timeframe', 'H1')
    asset = request.query_params.get('asset', 'USD')
    lang = request.query_params.get('lang', 'fa')
    
    try:
        # Get analysis service
        service = get_analysis_service()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            service.generate_daily_summary(
                timeframe=timeframe,
                asset=asset,
                lang=lang
            )
        )
        loop.close()
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'generated_at': datetime.now().isoformat(),
            'articles_count': 0,
            'timeframe': timeframe,
            'asset': asset,
            'lang': lang,
            'summary': f'Error generating summary: {str(e)}',
            'sources': [],
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_timeframes(request):
    """Get available timeframes and trading styles"""
    # Import from existing config
    try:
        from config.timeframes import TIMEFRAME_NAMES, TRADING_STYLES
        return Response({
            'timeframes': TIMEFRAME_NAMES,
            'trading_styles': TRADING_STYLES
        })
    except ImportError:
        return Response({
            'timeframes': {
                'M1': '1 Minute', 'M5': '5 Minutes', 'M15': '15 Minutes',
                'M30': '30 Minutes', 'H1': '1 Hour', 'H4': '4 Hours',
                'D1': 'Daily', 'W1': 'Weekly', 'MN': 'Monthly'
            },
            'trading_styles': {
                'scalping': {'name': 'Scalping', 'timeframes': ['M1', 'M5', 'M15']},
                'day_trading': {'name': 'Day Trading', 'timeframes': ['M15', 'M30', 'H1']},
                'swing_trading': {'name': 'Swing Trading', 'timeframes': ['H1', 'H4', 'D1']},
                'position_trading': {'name': 'Position Trading', 'timeframes': ['D1', 'W1', 'MN']}
            }
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_mtf_analysis(request, pair):
    """Get Multi-Timeframe Analysis"""
    pair = pair.upper()
    pairs = get_pairs_config()
    
    if pair not in pairs:
        return Response(
            {'detail': f'Pair {pair} not configured'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    timeframes = request.query_params.get('timeframes', 'H1').split(',')
    trading_style = request.query_params.get('trading_style', 'day')
    
    # TODO: PRIORITY_NEXT - Implement MTF analysis with llm/analyzer.py
    return Response({
        'pair': pair,
        'timeframes': timeframes,
        'trading_style': trading_style,
        'analysis': {
            'note': 'Multi-timeframe analysis pending - see TODO comments'
        },
        'generated_at': datetime.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def translate_text(request):
    """Translate text to target language"""
    text = request.data.get('text', '')
    target_lang = request.data.get('target_lang', 'fa')
    
    # TODO: PRIORITY_NEXT - Integrate with llm/analyzer.py for translation
    return Response({
        'original': text,
        'translated': text,  # Placeholder
        'target_lang': target_lang,
        'note': 'Translation integration pending'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_chart_image(request):
    """Analyze chart image using AI Vision"""
    import asyncio
    from .services import get_analysis_service
    
    pair = request.data.get('pair', '').upper()
    image_data = request.data.get('image_data', '')  # base64 encoded
    timeframe = request.data.get('timeframe', 'H1')
    trading_style = request.data.get('trading_style', 'day')
    
    if not pair:
        return Response(
            {'detail': 'Pair is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not image_data:
        return Response(
            {'detail': 'Image data is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = get_analysis_service()
        
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                service.analyze_chart_image(pair, image_data, timeframe, trading_style)
            )
        finally:
            loop.close()
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Chart image analysis error: {str(e)}")
        return Response({
            'error': str(e),
            'pair': pair,
            'analysis': {
                'sentiment': 'Unknown',
                'sentiment_score': 0,
                'key_factors': [f'خطا: {str(e)}'],
            },
            'recommendation': {
                'recommendation': 'WAIT',
                'confidence': 0,
                'reasoning': f'خطا در تحلیل: {str(e)}',
            },
            'generated_at': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
