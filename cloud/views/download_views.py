import os
from django.http import FileResponse
from rest_framework import status
from cloud.models import User, File
from cloud_disk_backend.global_function import method_check, json_response
from uuid import UUID


@method_check(['GET'])
def download_small_file_content(request):
    """根据文件 ID 下载小文件内容。"""
    # 获取用户 ID 和文件 ID
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    file_id = request.GET.get('file_id')  # 改用查询参数

    if not user_id or not file_id:
        return json_response('', '缺少用户 ID 或文件 ID', status.HTTP_400_BAD_REQUEST)

    # 验证 user_id 和 file_id 是否是有效的 UUID
    try:
        user_id = UUID(user_id)
        file_id = UUID(file_id)
    except ValueError:
        return json_response('', '无效的用户 ID 或文件 ID', status.HTTP_400_BAD_REQUEST)

    # 查询用户和文件
    try:
        user = User.objects.get(uuid=user_id)
        file_instance = File.objects.get(file_id=file_id, uuid=user, is_chunked=False)
    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)
    except File.DoesNotExist:
        return json_response('', '文件不存在或不属于该用户', status.HTTP_404_NOT_FOUND)

    # 检查文件是否存在于文件系统
    file_path = file_instance.path
    if not os.path.exists(file_path):
        return json_response('', '文件系统中未找到文件', status.HTTP_404_NOT_FOUND)

    # 返回文件流响应
    try:
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_instance.name)
        response['Content-Length'] = file_instance.size
        return response
    except IOError:
        return json_response('', '文件读取出错', status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return json_response('', f'文件下载出错: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)
