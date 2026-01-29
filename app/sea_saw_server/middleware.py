"""
Custom middleware for Sea-Saw application
"""


class DisableCSRFForAPIMiddleware:
    """
    Disable CSRF protection for API endpoints that use JWT authentication.

    Since JWT tokens are sent via Authorization header (not cookies),
    they are not vulnerable to CSRF attacks. This middleware disables
    CSRF checks for API endpoints while keeping it enabled for admin panel.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Disable CSRF for API endpoints
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)

        response = self.get_response(request)
        return response
