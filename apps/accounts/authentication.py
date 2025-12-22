"""
Custom Token Authentication for REST Framework
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import AuthToken


class TokenAuthentication(BaseAuthentication):
    """Token-based authentication using Bearer token"""
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith(f'{self.keyword} '):
            return None
        
        token = auth_header[len(self.keyword) + 1:]
        
        try:
            auth_token = AuthToken.objects.select_related('user').get(token=token)
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
        
        if not auth_token.is_valid():
            raise AuthenticationFailed('Token expired or inactive')
        
        if not auth_token.user.is_active:
            raise AuthenticationFailed('User account is disabled')
        
        return (auth_token.user, auth_token)
    
    def authenticate_header(self, request):
        return self.keyword
