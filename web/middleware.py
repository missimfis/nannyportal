import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def _parse_rate(value, default_limit, default_window):
    try:
        limit_s, window_s = str(value).split('/', 1)
        return max(1, int(limit_s)), max(1, int(window_s))
    except Exception:
        return default_limit, default_window


class SimpleRateLimitMiddleware:
    """Best-effort request throttling for abuse-prone endpoints.

    This is a lightweight in-app limiter (cache-backed). For multi-instance
    production deployments use a shared cache (Redis/Memcached) and/or edge/WAF
    rate limiting.
    """

    RULES = {
        ('POST', 'login'): ('RATE_LIMIT_LOGIN', 10, 300),
        ('POST', 'password_reset'): ('RATE_LIMIT_PASSWORD_RESET', 5, 900),
        ('POST', 'web:create-user'): ('RATE_LIMIT_SIGNUP', 10, 3600),
        ('POST', 'web:contact'): ('RATE_LIMIT_CONTACT', 10, 3600),
        ('POST', 'web:nachrichten'): ('RATE_LIMIT_MESSAGE', 60, 300),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('POST',):
            match = getattr(request, 'resolver_match', None)
            if match is None:
                try:
                    match = request.resolver_match
                except Exception:
                    match = None
            # Resolve lazily if not yet resolved
            view_name = None
            try:
                from django.urls import resolve
                match = match or resolve(request.path_info)
                view_name = match.view_name
            except Exception:
                view_name = None

            rule = self.RULES.get((request.method, view_name))
            if rule:
                setting_name, dlim, dwin = rule
                limit, window = _parse_rate(getattr(settings, setting_name, None), dlim, dwin)
                ident = self._client_ip(request)
                key = f"rl:{view_name}:{ident}:{int(time.time() // window)}"
                try:
                    count = cache.get(key, 0) + 1
                    cache.set(key, count, timeout=window)
                except Exception:
                    count = 1
                if count > limit:
                    resp = HttpResponse('Too many requests. Please try again later.', status=429)
                    resp['Retry-After'] = str(window)
                    return resp

        return self.get_response(request)

    @staticmethod
    def _client_ip(request):
        # Trust X-Forwarded-For only when configured via proxy headers at deployment.
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff and getattr(settings, 'SECURE_PROXY_SSL_HEADER', None):
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
