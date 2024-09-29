# bookings/middleware.py

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import re
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware
from django.http import JsonResponse
from django.http import HttpResponseBadRequest


class CleanRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Clean the path of the request
        cleaned_path = re.sub(r'\s+', '', request.path)
        request.path = cleaned_path


# bookings/middleware.py
class CSRFMiddlewareDebug(MiddlewareMixin):
    def process_request(self, request):
        print("CSRF Token in request:", request.META.get('CSRF_COOKIE'))
        return None
    
class CustomCSRFMiddleware(CsrfViewMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:  # Methods that require CSRF
            return super().process_view(request, view_func, view_args, view_kwargs)
        return None

    def _reject(self, request, reason):
        # Customize the response when CSRF validation fails
        return JsonResponse({'error': 'CSRF token missing or incorrect.'}, status=403)

class RemoveNewlinesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Remove newlines from request path
        cleaned_path = re.sub(r'%0A', '', request.path).strip()

        if cleaned_path != request.path:
            # Redirect to cleaned path or raise error if necessary
            request.path_info = cleaned_path
        
        response = self.get_response(request)
        return response




