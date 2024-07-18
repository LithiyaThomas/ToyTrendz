from django.shortcuts import redirect

class AdminRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude the admin-login URL from the redirection rule
        if request.path.startswith('/admin_panel/') and not request.path.endswith('admin-login/') and not request.session.get('is_admin'):
            return redirect('admin-login')
        return self.get_response(request)
