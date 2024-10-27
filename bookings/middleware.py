import re
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware
from django.http import JsonResponse
from django.http import HttpResponseBadRequest
from django.middleware.csrf import get_token
from django.test import TestCase
from django.urls import reverse


class CleanRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cleaned_path = re.sub(r'\s+', '', request.path)
        request.path = cleaned_path


class CSRFMiddlewareDebug(MiddlewareMixin):
    def process_request(self, request):
        print("CSRF Token in request:", request.META.get('CSRF_COOKIE'))
        return None
    
class CustomCSRFMiddleware(CsrfViewMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:  
            return super().process_view(request, view_func, view_args, view_kwargs)
        return None

    def _reject(self, request, reason):
        return JsonResponse({'error': 'CSRF token missing or incorrect.'}, status=403)

class RemoveNewlinesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cleaned_path = re.sub(r'%0A', '', request.path).strip()

        if cleaned_path != request.path:
            request.path_info = cleaned_path
        
        response = self.get_response(request)
        return response

class CsrfTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.csrf_token = get_token(self.client)

    def test_valid_csrf_token(self):
        response = self.client.post(reverse('create-bus'), data={}, HTTP_X_CSRFTOKEN=self.csrf_token)
        self.assertEqual(response.status_code, 200)



