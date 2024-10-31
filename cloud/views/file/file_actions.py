# 文件上传、下载、重命名、元数据获取
import os
import uuid

from django.http import FileResponse
from rest_framework import status
from uuid import UUID

from cloud_disk_backend import settings
from cloud_disk_backend.global_function import json_response, method_check
from cloud.models import User, Folder, File

# 静态变量
CHUNK_THRESHOLD = 10 * 1024 * 1024  # 分片阈值为 10MB


def get_unique_filename(folder, file_name, user):
    """检查同一文件夹中是否存在同名文件，若存在则添加后缀直到生成唯一文件名"""
    base_name, ext = os.path.splitext(file_name)  # 分离文件名和扩展名
    counter = 1
    unique_name = file_name

    while File.objects.filter(name=unique_name, folder_id=folder, uuid=user).exists():
        unique_name = f"{base_name}_{counter}{ext}"
        counter += 1

    return unique_name


@method_check(["POST"])
def upload_small_file(request):
    # 验证输入参数
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    folder_id = request.POST.get('folder_id')
    file_name = request.POST.get('file_name')
    file_sha256 = request.POST.get('file_sha256')
    if not all([user_id, folder_id, file_name, file_sha256]):
        return json_response('', '缺少必要参数', status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(uuid=user_id)  # 获取用户
        folder = Folder.objects.get(folder_id=folder_id, uuid=user)  # 获取文件夹
    except (User.DoesNotExist, Folder.DoesNotExist):
        return json_response('', '用户或文件夹不存在', status.HTTP_404_NOT_FOUND)

    # 获取上传的文件
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return json_response('', '文件不存在', status.HTTP_400_BAD_REQUEST)

    # 校验文件大小（不超过 10MB）
    if uploaded_file.size > CHUNK_THRESHOLD:
        return json_response('', '文件大小超过分片阈值', status.HTTP_400_BAD_REQUEST)

    # 获取唯一文件名
    unique_file_name = get_unique_filename(folder, file_name, user)

    # 获取文件大小
    file_size = uploaded_file.size

    # 重命名文件为 file_id
    file_id = uuid.uuid4()
    new_file_name = str(file_id)

    # 保存文件
    user_root_dir = os.path.join(settings.MEDIA_ROOT, str(user.uuid))
    file_path = os.path.join(user_root_dir, new_file_name)
    os.makedirs(user_root_dir, exist_ok=True)  # 确保用户目录存在

    # 将上传的文件保存到指定路径
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    # 创建 File 实例并保存到数据库
    new_file = File(
        file_id=file_id,
        name=unique_file_name,  # 使用唯一文件名
        size=file_size,
        folder_id=folder,
        uuid=user,
        path=file_path,
        file_sha256=file_sha256,
        is_complete=True
    )
    new_file.save()
    return json_response({"file_id": str(new_file.file_id)}, '小文件上传成功', status.HTTP_201_CREATED)


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
        user_id = uuid.UUID(user_id)
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