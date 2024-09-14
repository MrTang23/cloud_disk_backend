# 创建中间件，进行鉴权
from rest_framework import status
from cloud.models import TempToken
from cloud_disk_backend import global_function


# 验证请求头中token是否有效
def check_token_validity(request):
    token_str = request.META.get('HTTP_AMOS_CLOUD_TOKEN')
    try:
        # 获取 Token 实例
        token = TempToken.objects.get(token=token_str)

        # 检查 token 是否有效
        if token.is_valid():
            # 返回用户名
            return token.user.username
        else:
            return None
    except TempToken.DoesNotExist:
        return None


class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        excluded_paths = ['/login', '/register']  # 不需要鉴权的路径列表
        if request.path in excluded_paths:
            response = self.get_response(request)
        else:
            check_result = check_token_validity(request)
            if check_result:
                response = self.get_response(request, check_result)
            else:
                response = global_function.json_response('', 'token已过期或不存在，请重新登陆',
                                                         status.HTTP_401_UNAUTHORIZED)
        return response
