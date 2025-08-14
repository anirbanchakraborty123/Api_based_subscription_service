import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests and responses."""
    
    def process_request(self, request):
        """Log incoming request details."""
        request.start_time = time.time()
        
        if request.path.startswith('/api/'):
            logger.info(
                f"API Request: {request.method} {request.path} "
                f"- User: {getattr(request.user, 'username', 'Anonymous')} "
                f"- IP: {self.get_client_ip(request)}"
            )
        
        return None
    
    def process_response(self, request, response):
        """Log response details and request duration."""
        if hasattr(request, 'start_time') and request.path.startswith('/api/'):
            duration = time.time() - request.start_time
            
            logger.info(
                f"API Response: {request.method} {request.path} "
                f"- Status: {response.status_code} "
                f"- Duration: {duration:.3f}s "
                f"- User: {getattr(request.user, 'username', 'Anonymous')}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for API errors."""
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        request = context.get('request')
        user = getattr(request, 'user', 'Anonymous')
        
        logger.error(
            f"API Exception: {exc.__class__.__name__} "
            f"- User: {getattr(user, 'username', 'Anonymous')} "
            f"- Path: {getattr(request, 'path', 'Unknown')} "
            f"- Method: {getattr(request, 'method', 'Unknown')} "
            f"- Error: {str(exc)}"
        )
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Add specific error messages for common cases
        if response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Invalid request data'
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data['message'] = 'Too many requests. Please try again later.'
        
        response.data = custom_response_data
    
    return response