"""
Views for Accounts App
"""
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User, AuthToken
from .serializers import UserSerializer, SignUpSerializer, SignInSerializer


# ============== Page Views ==============

def landing_page(request):
    """Landing page - shown before login"""
    return render(request, 'landing.html')


def dashboard(request):
    """Main dashboard - shown after login"""
    # Load pairs from configuration
    from apps.analysis.views import get_pairs_config
    pairs = get_pairs_config()
    
    return render(request, 'index.html', {
        'title': 'Forex Analysis Assistant',
        'pairs': list(pairs.keys())
    })


def pricing_page(request):
    """Pricing page"""
    return render(request, 'pricing.html')


def thank_you_page(request):
    """Thank you page after subscription purchase"""
    return render(request, 'thank-you.html')


def features_page(request):
    """Features page"""
    return render(request, 'features.html')


def resources_page(request):
    """Resources page"""
    return render(request, 'resources.html')


def assets_page(request):
    """Assets page"""
    return render(request, 'assets.html')


def signup_page(request):
    """Sign up page"""
    return render(request, 'signup.html')


def signin_page(request):
    """Sign in page"""
    return render(request, 'signin.html')


def chart_view(request):
    """Chart view page"""
    return render(request, 'chart_view.html')


# ============== API Views ==============

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    """Register a new user"""
    serializer = SignUpSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = serializer.save()
    
    # Create auth token
    token = AuthToken.objects.create(
        user=user,
        token=AuthToken.generate_token()
    )
    
    return Response({
        'user': UserSerializer(user).data,
        'token': token.token
    }, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
    """Login user"""
    serializer = SignInSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = serializer.validated_data['user']
    remember_me = serializer.validated_data.get('remember_me', False)
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Create auth token
    expires_at = None
    if not remember_me:
        expires_at = timezone.now() + timedelta(days=7)
    
    token = AuthToken.objects.create(
        user=user,
        token=AuthToken.generate_token(),
        expires_at=expires_at
    )
    
    return Response({
        'user': UserSerializer(user).data,
        'token': token.token
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user and invalidate token"""
    if hasattr(request, 'auth') and isinstance(request.auth, AuthToken):
        request.auth.is_active = False
        request.auth.save(update_fields=['is_active'])
    
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current user info"""
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })
