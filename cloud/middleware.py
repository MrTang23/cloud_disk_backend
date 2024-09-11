# 创建中间件，进行鉴权
import json
from datetime import datetime
from hashlib import md5

from django.utils import timezone
from rest_framework import status

from cloud_disk_backend import global_function

from cloud import models as cloud_models


# md5加密
def to_md5(string_name):
    md5_object = md5()
    md5_object.update(string_name.encode(encoding='utf-8'))
    return md5_object.hexdigest()


# 验证请求头中token是否有效
def check_token(request):
    token = request.META.get('HTTP_AMOS_CLOUD_TOKEN')
    # 验证token时同时对md5加密后的用户名和数据库中token对应的用户名匹配检查
    username_md5 = request.META.get('HTTP_AMOS_CLOUD_USER')
    if cloud_models.Token.objects.filter(token=token).exists():
        token_queryset = cloud_models.Token.objects.get(token=token)
        if to_md5(token_queryset.username) == username_md5:
            # 计算时间差
            current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
            token_start_time = datetime.strptime(token_queryset.start_time, "%Y-%m-%d %H:%M:%S")
            time_difference = (current_time - token_start_time).total_seconds() / 3600
            # 时间差大于7*24着返回false并删除该token
            if time_difference > 7 * 24:
                cloud_models.Token.objects.filter(token=token).delete()
                return False
            # token通过则返回用户名
            return token_queryset.username
        else:
            return False
    else:
        return False


def preprocess_request(request):
    # 在这里对请求执行操作
    data = json.loads(request.body)
    check_result = check_token(request)
    if check_result:
        print(data)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_401_UNAUTHORIZED)


class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 在视图处理请求之前执行操作
        data = json.loads(request.body)
        check_result = check_token(request)
        if check_result:
            # 调用视图（处理请求）
            response = self.get_response(data, check_result)
            # 如果需要，也可以在此处对响应进行处理
            return response
        else:
            return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_401_UNAUTHORIZED)
