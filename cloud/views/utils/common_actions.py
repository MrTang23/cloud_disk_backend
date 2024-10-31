import re
import uuid

from django.db import transaction
from rest_framework import status
from cloud_disk_backend.global_function import json_response, method_check
from cloud.models import User, Folder, File


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