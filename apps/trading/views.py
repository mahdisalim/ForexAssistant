"""
Views for Trading App
# TODO: PRIORITY_NEXT - Integrate with existing trading/ and web/services/ modules
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TradingAccount, TradingRobot


# ============== Trading Accounts API ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_trading_accounts(request):
    """Get all trading accounts for the current user"""
    accounts = TradingAccount.objects.filter(user=request.user)
    
    return Response({
        'accounts': [
            {
                'id': str(acc.id),
                'broker': acc.broker,
                'login': acc.login,
                'server': acc.server,
                'nickname': acc.nickname,
                'balance': float(acc.balance),
                'equity': float(acc.equity),
                'currency': acc.currency,
                'risk_percent': acc.risk_percent,
                'is_connected': acc.is_connected,
                'last_connected': acc.last_connected.isoformat() if acc.last_connected else None,
            }
            for acc in accounts
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_trading_account(request):
    """Add a new trading account"""
    # TODO: PRIORITY_NEXT - Integrate with web/services/trading_accounts.py
    # and web/services/broker_connectors.py for actual broker connection
    
    broker = request.data.get('broker')
    login = request.data.get('login')
    password = request.data.get('password')
    server = request.data.get('server')
    risk_percent = request.data.get('risk_percent', 2.0)
    nickname = request.data.get('nickname', '')
    
    if not all([broker, login, password, server]):
        return Response(
            {'detail': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if account already exists
    if TradingAccount.objects.filter(
        user=request.user, broker=broker, login=login, server=server
    ).exists():
        return Response(
            {'detail': 'Account already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: PRIORITY_NEXT - Encrypt password using web/services/encryption.py
    # TODO: PRIORITY_NEXT - Connect to broker and verify credentials
    
    account = TradingAccount.objects.create(
        user=request.user,
        broker=broker,
        login=login,
        server=server,
        nickname=nickname,
        risk_percent=risk_percent,
        # password_encrypted=encrypt(password)  # TODO
    )
    
    return Response({
        'success': True,
        'account': {
            'id': str(account.id),
            'broker': account.broker,
            'login': account.login,
            'server': account.server,
            'nickname': account.nickname,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_trading_account(request, account_id):
    """Refresh account information by reconnecting to broker"""
    try:
        account = TradingAccount.objects.get(id=account_id, user=request.user)
    except TradingAccount.DoesNotExist:
        return Response(
            {'detail': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # TODO: PRIORITY_NEXT - Reconnect to broker and update account info
    return Response({
        'success': True,
        'message': 'Account refresh pending - broker integration needed'
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_trading_account(request, account_id):
    """Delete a trading account"""
    try:
        account = TradingAccount.objects.get(id=account_id, user=request.user)
    except TradingAccount.DoesNotExist:
        return Response(
            {'detail': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    account.delete()
    return Response({'success': True, 'message': 'Account deleted'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_account_risk(request, account_id):
    """Update risk percentage for an account"""
    try:
        account = TradingAccount.objects.get(id=account_id, user=request.user)
    except TradingAccount.DoesNotExist:
        return Response(
            {'detail': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    risk_percent = request.data.get('risk_percent')
    if risk_percent is not None:
        account.risk_percent = risk_percent
        account.save(update_fields=['risk_percent'])
    
    return Response({'success': True, 'risk_percent': account.risk_percent})


# ============== Trading Robots API ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_robots(request):
    """Get available robots and strategies"""
    # TODO: PRIORITY_NEXT - Integrate with trading/unified_robots.py
    
    return Response({
        'robots': [
            {'name': 'stochastic', 'description': 'Stochastic Oscillator Robot', 'available': True},
            {'name': 'rsi', 'description': 'RSI Robot', 'available': True},
        ],
        'sl_strategies': ['fixed', 'atr', 'swing', 'percentage'],
        'tp_strategies': ['fixed', 'risk_reward', 'atr', 'swing'],
        'timeframes': ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN'],
        'subscription': request.user.subscription_plan
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_robots(request):
    """Get user's active robots"""
    robots = TradingRobot.objects.filter(user=request.user)
    
    return Response({
        'robots': [
            {
                'id': str(robot.id),
                'name': robot.name,
                'robot_type': robot.robot_type,
                'symbol': robot.symbol,
                'timeframe': robot.timeframe,
                'sl_strategy': robot.sl_strategy,
                'tp_strategy': robot.tp_strategy,
                'risk_percent': robot.risk_percent,
                'is_active': robot.is_active,
                'total_trades': robot.total_trades,
                'winning_trades': robot.winning_trades,
            }
            for robot in robots
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_robot(request):
    """Create a new trading robot"""
    # TODO: PRIORITY_NEXT - Integrate with trading/robot_manager.py
    
    robot = TradingRobot.objects.create(
        user=request.user,
        name=request.data.get('robot_name', 'New Robot'),
        robot_type=request.data.get('robot_type', 'stochastic'),
        symbol=request.data.get('symbol', 'EURUSD'),
        timeframe=request.data.get('timeframe', 'H1'),
        sl_strategy=request.data.get('sl_strategy', 'atr'),
        tp_strategy=request.data.get('tp_strategy', 'risk_reward'),
        sl_params=request.data.get('sl_params', {}),
        tp_params=request.data.get('tp_params', {}),
        risk_percent=request.data.get('risk_percent', 1.0),
    )
    
    return Response({
        'success': True,
        'robot': {
            'id': str(robot.id),
            'name': robot.name,
            'robot_type': robot.robot_type,
        }
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_robot(request, robot_id):
    """Update robot configuration"""
    try:
        robot = TradingRobot.objects.get(id=robot_id, user=request.user)
    except TradingRobot.DoesNotExist:
        return Response(
            {'detail': 'Robot not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update fields
    for field in ['sl_strategy', 'tp_strategy', 'sl_params', 'tp_params', 'risk_percent', 'is_active']:
        if field in request.data:
            setattr(robot, field, request.data[field])
    
    robot.save()
    
    return Response({'success': True, 'message': 'Robot updated'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_robot(request, robot_id):
    """Delete a robot"""
    try:
        robot = TradingRobot.objects.get(id=robot_id, user=request.user)
    except TradingRobot.DoesNotExist:
        return Response(
            {'detail': 'Robot not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    robot.delete()
    return Response({'success': True, 'message': 'Robot deleted'})
