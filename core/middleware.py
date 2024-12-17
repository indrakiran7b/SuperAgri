# core/middleware.py
from django.core.cache import cache
from django.http import HttpResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            ip = request.META.get('REMOTE_ADDR')
            requests = cache.get(f'requests_{ip}', 0)
            
            if requests >= 100:  # 100 requests per hour limit
                return HttpResponse(
                    'Rate limit exceeded. Please try again later.',
                    status=429  # 429 is the status code for Too Many Requests
                )
            
            cache.set(f'requests_{ip}', requests + 1, 3600)  # 1 hour expiry
        
        return self.get_response(request)