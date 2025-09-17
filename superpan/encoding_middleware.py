"""
Middleware для правильной работы с UTF-8 кодировкой
"""

class UTF8EncodingMiddleware:
    """Middleware для принудительной установки UTF-8 кодировки"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Принудительно устанавливаем UTF-8 кодировку
        if 'Content-Type' in response:
            content_type = response['Content-Type']
            if 'charset=' not in content_type and 'text/' in content_type:
                response['Content-Type'] = f"{content_type}; charset=utf-8"
        elif response.get('Content-Type', '').startswith('text/'):
            response['Content-Type'] = f"{response['Content-Type']}; charset=utf-8"
        
        return response
