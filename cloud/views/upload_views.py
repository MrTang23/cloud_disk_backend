import json
import os
import re
import uuid

from django.db import transaction
from rest_framework import status
from cloud_disk_backend import settings
from cloud_disk_backend.global_function import json_response, method_check
from cloud.models import User, Folder, File

# 静态变量
CHUNK_THRESHOLD = 10 * 1024 * 1024  # 分片阈值为 10MB


def validate_name(name):
    """
    校验文件或文件夹名称的合法性。
    :param name: 文件或文件夹的名称
    :return: (bool, str) - 是否合法及错误信息
    """
    if not (1 <= len(name) <= 255):
        return False, "名称长度必须在 1 到 255 个字符之间"
    if re.search(r'[/:*?"<>|]', name):
        return False, "名称中包含不允许的特殊字符 / \\ : * ? \" < > |"
    if name.strip() == "":
        return False, "名称不能仅包含空格"
    return True, ""


def get_unique_filename(folder, file_name, user):
    """检查同一文件夹中是否存在同名文件，若存在则添加后缀直到生成唯一文件名"""
    base_name, ext = os.path.splitext(file_name)  # 分离文件名和扩展名
    counter = 1
    unique_name = file_name

    while File.objects.filter(name=unique_name, folder_id=folder, uuid=user).exists():
        unique_name = f"{base_name}_{counter}{ext}"
        counter += 1

    return unique_name


# 新建文件夹
@method_check(["POST"])
def new_folder(request):
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    data = json.loads(request.body)
    folder_name = data.get('folder_name')
    parent_folder_id = data.get('parent_folder_id')

    try:
        # 查询用户是否存在
        user = User.objects.get(uuid=user_id)
    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)

    # 校验文件夹名称是否为空
    if not folder_name:
        return json_response('', '文件夹名称不能为空', status.HTTP_400_BAD_REQUEST)

    # 校验文件夹名称长度
    if len(folder_name) < 1 or len(folder_name) > 255:
        return json_response('', '文件夹名称长度应在1到255字符之间', status.HTTP_400_BAD_REQUEST)

    # 校验是否包含非法字符（正则表达式）
    # 文件夹名称只允许字母、数字、空格、下划线和横线
    if not re.match(r'^[\w\-\s]+$', folder_name):
        return json_response('', '文件夹名称包含非法字符', status.HTTP_400_BAD_REQUEST)

    if parent_folder_id:
        try:
            # 查询父文件夹是否存在
            parent_folder = Folder.objects.get(folder_id=parent_folder_id, uuid=user)
        except Folder.DoesNotExist:
            return json_response('', '父文件夹不存在', status.HTTP_404_NOT_FOUND)

        # 检查文件夹名称是否已存在于父文件夹中
        if Folder.objects.filter(name=folder_name, parent_folder_id=parent_folder, uuid=user).exists():
            return json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return json_response('', '禁止在该路径创建文件夹', status.HTTP_405_METHOD_NOT_ALLOWED)

    # 创建新文件夹
    Folder.objects.create(
        name=folder_name,
        uuid=user,
        parent_folder_id=parent_folder
    )

    return json_response('', '新建文件夹成功', status.HTTP_201_CREATED)


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


@method_check(['PATCH'])
@transaction.atomic
def rename_item(request):
    """
    通用重命名接口，根据类型对文件或文件夹进行重命名。
    """
    item_id = request.GET.get('id')
    new_name = request.GET.get('new_name')
    item_type = request.GET.get('type')  # 'file' 或 'folder'
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')

    # 基本参数检查
    if not all([item_id, new_name, item_type, user_id]):
        return json_response('', '缺少必要参数', status.HTTP_400_BAD_REQUEST)

    if item_type not in ['file', 'folder']:
        return json_response('', '无效的类型参数', status.HTTP_400_BAD_REQUEST)

    # 名称合法性校验
    is_valid, error_msg = validate_name(new_name)
    if not is_valid:
        return json_response('', error_msg, status.HTTP_400_BAD_REQUEST)

    try:
        item_id = uuid.UUID(item_id)
        user_id = uuid.UUID(user_id)
    except ValueError:
        return json_response('', '无效的 ID 格式', status.HTTP_400_BAD_REQUEST)

    # 查询用户和文件/文件夹对象
    try:
        user = User.objects.get(uuid=user_id)

        # 根据类型获取对象并校验存在性、重命名限制和重名情况
        if item_type == 'folder':
            item = Folder.objects.filter(folder_id=item_id, uuid=user).first()
            if not item:
                return json_response('', '文件夹不存在', status.HTTP_404_NOT_FOUND)
            if item.parent_folder_id is None or item.name == "回收站":
                return json_response('', '无法重命名根文件夹或回收站', status.HTTP_400_BAD_REQUEST)
            if Folder.objects.filter(parent_folder_id=item.parent_folder_id, name=new_name, uuid=user).exists():
                return json_response('', '同一目录下已有相同名称的文件夹', status.HTTP_400_BAD_REQUEST)
        else:
            item = File.objects.filter(file_id=item_id, uuid=user).first()
            if not item:
                return json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
            if File.objects.filter(folder_id=item.folder_id, name=new_name, uuid=user).exists():
                return json_response('', '同一目录下已有相同名称的文件', status.HTTP_400_BAD_REQUEST)

        # 执行重命名
        item.name = new_name
        item.save()
        return json_response('', f'{item_type.capitalize()} 重命名成功', status.HTTP_200_OK)

    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return json_response('', f'发生错误: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)
