from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_http_methods
from rest_framework import status
from uuid import UUID

from cloud_disk_backend import global_function
from cloud.models import User, Folder, File


@require_http_methods(["GET"])
def get_file_metadata(request):
    """获取文件的元信息，包括下载链接和 SHA-256 校验和。"""
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    file_id = request.GET.get('file_id')

    # 验证用户 ID 和文件 ID 格式
    try:
        user_id = UUID(user_id)
        file_id = UUID(file_id)
    except ValueError:
        return global_function.json_response('', '无效的用户或文件 ID', status.HTTP_400_BAD_REQUEST)

    # 查询用户和文件
    try:
        user = User.objects.get(uuid=user_id)
        file_instance = File.objects.get(file_id=file_id, uuid=user, is_chunked=False)  # 获取文件对象
    except (User.DoesNotExist, File.DoesNotExist):
        return global_function.json_response('', '用户或文件不存在', status.HTTP_404_NOT_FOUND)

    # 构建文件下载链接
    download_url = f"{request.build_absolute_uri('/download/?file_id=')}{file_instance.file_id}/"

    # 返回文件元数据
    return global_function.json_response({
        "file_name": file_instance.name,
        "file_size": global_function.human_readable_size(file_instance.size),
        "file_sha256": file_instance.file_sha256,
        "download_url": download_url
    }, '获取文件元数据', status.HTTP_200_OK)


# 获取某目录下文件列表
def get_filelist(request):
    # 从请求头获取用户ID
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    parent_folder_id = request.GET.get('parent_folder_id')

    # 初始化文件列表
    file_list = []

    # 批量获取文件夹和文件列表
    subfolders = Folder.objects.filter(uuid=user_id, parent_folder_id=parent_folder_id).only('folder_id',
                                                                                             'name',
                                                                                             'created_at')
    subfiles = File.objects.filter(uuid=user_id, folder_id=parent_folder_id).only('file_id', 'name',
                                                                                  'size',
                                                                                  'updated_at')

    # 填充文件夹列表
    for folder in subfolders:
        temp_folder_obj = {
            'id': str(folder.folder_id),  # 文件夹的ID
            'name': folder.name,  # 文件夹的名称
            'type': '文件夹',  # 标识类型为文件夹
            'size': '--',  # 文件夹没有大小，使用 '--' 或者 0 表示
            'lastModifiedTime': folder.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # 使用文件夹的创建时间作为修改时间
        }
        file_list.append(temp_folder_obj)

    # 填充文件列表
    for file in subfiles:
        temp_file_obj = {
            'id': str(file.file_id),  # 文件的ID
            'name': file.name,  # 文件的名称
            'type': global_function.get_file_type(file.name),  # 根据文件名获取文件类型
            'size': global_function.human_readable_size(file.size),  # 文件的大小转换为易读格式
            'lastModifiedTime': file.updated_at.strftime('%Y-%m-%d %H:%M:%S'),  # 文件的最后修改时间
        }
        file_list.append(temp_file_obj)

    # 返回文件列表作为响应
    return global_function.json_response(file_list, '获取文件列表成功', status.HTTP_200_OK)


def find_user(request):
    identifier = request.GET.get('identifier')
    if not identifier:
        return global_function.json_response('', '请提供一个标识符', status.HTTP_400_BAD_REQUEST)

    try:
        # 尝试查找用户名
        User.objects.get(username=identifier)
        return global_function.json_response('username', '标识符为用户名', status.HTTP_200_OK)
    except ObjectDoesNotExist:
        pass  # 如果未找到用户名，继续尝试邮箱查找

    try:
        # 尝试查找邮箱
        User.objects.get(email=identifier)
        return global_function.json_response('email', '标识符为邮箱', status.HTTP_200_OK)
    except ObjectDoesNotExist:
        pass  # 如果未找到邮箱，返回不存在的信息

    return global_function.json_response('', '该标识符不存在与用户表中', status.HTTP_404_NOT_FOUND)
