import os
from rest_framework import status
from uuid import UUID
from cloud.models import TempToken, User
from cloud_disk_backend import global_function, settings

EXCLUDED_PATHS = ['/auth/login', '/auth/register', '/query/find_user', '/query/echo_request']
INVALID_TOKEN_MSG = 'Token 或用户 ID 无效或不匹配，请检查后重试。'
FILE_SYSTEM_ERROR_MSG = '后端文件系统损坏'


def check_file_system():
    """检查后端文件系统是否完整"""
    return os.path.exists(settings.MEDIA_ROOT)


def check_token_validity(request):
    """验证请求头中token是否有效，若令牌过期则自动删除"""
    token_str = request.META.get('HTTP_AMOS_CLOUD_TOKEN')
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')

    # 验证 user_id 是否是有效的 UUID
    try:
        user_id = UUID(user_id)
    except (ValueError, TypeError):
        return False

    # 查找 User 实例
    user = User.objects.filter(uuid=user_id).first()
    if not user:
        return False

    # 查询 TempToken 表，检查是否存在与 token_str 和 user_id 匹配的记录
    temp_token = TempToken.objects.filter(token=token_str, uuid=user).first()

    # 如果令牌存在，检查其有效性，过期则删除
    if temp_token:
        if temp_token.is_valid():
            return True
        else:
            # 令牌已过期，自动删除
            temp_token.delete()

    return False


class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not check_file_system():
            return global_function.json_response('', FILE_SYSTEM_ERROR_MSG, status.HTTP_400_BAD_REQUEST)

        if request.path in EXCLUDED_PATHS:
            return self.get_response(request)

        if check_token_validity(request):
            return self.get_response(request)

        return global_function.json_response('', INVALID_TOKEN_MSG, status.HTTP_400_BAD_REQUEST)
