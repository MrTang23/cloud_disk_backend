# 创建中间件，进行鉴权
from rest_framework import status
from uuid import UUID

from cloud.models import TempToken, User
from cloud_disk_backend import global_function


# 验证请求头中token是否有效
def check_token_validity(request):
    token_str = request.META.get('HTTP_AMOS_CLOUD_TOKEN')
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')

    # 验证 user_id 是否是有效的 UUID
    try:
        user_id = UUID(user_id)
    except ValueError:
        return False

    # 查找 User 实例
    try:
        user = User.objects.get(uuid=user_id)
    except User.DoesNotExist:
        return False

    # 查询 TempToken 表，检查是否存在与 token_str 和 user_id 匹配的记录，并验证其有效性
    try:
        temp_token = TempToken.objects.get(token=token_str, uuid=user)
        return temp_token.is_valid()
    except TempToken.DoesNotExist:
        return False


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
                response = self.get_response(request)
            else:
                response = global_function.json_response('', 'Token 或用户 ID 无效或不匹配，请检查后重试。',
                                                         status.HTTP_400_BAD_REQUEST)
        return response
