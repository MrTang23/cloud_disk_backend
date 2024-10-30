from django.db import transaction
from cloud.models import Folder, User, File
from cloud_disk_backend.global_function import json_response, method_check
from rest_framework import status
from uuid import UUID


@method_check(['DELETE'])
@transaction.atomic
def move_folder_to_recycle_bin(request):
    # 从请求中获取文件夹 ID
    folder_id = request.GET.get('folder_id')
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')

    # 检查输入参数
    if not folder_id or not user_id:
        return json_response('', '缺少必要参数', status.HTTP_400_BAD_REQUEST)

    # 验证 UUID 格式
    try:
        user_id = UUID(user_id)
        folder_id = UUID(folder_id)
    except ValueError:
        return json_response('', '无效的用户 ID 或文件夹 ID 格式', status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(uuid=user_id)  # 获取用户
        folder = Folder.objects.get(folder_id=folder_id, uuid=user)  # 获取文件夹

        # 检查是否是根文件夹，无法删除根文件夹
        if folder.parent_folder_id is None:
            return json_response('', '无法删除根文件夹', status.HTTP_400_BAD_REQUEST)

        # 检查是否是回收站，无法删除回收站
        if folder.name == '回收站':
            return json_response('', '无法删除回收站', status.HTTP_400_BAD_REQUEST)

        # 将文件夹移动到回收站
        recycle_bin = Folder.objects.get(name='回收站', uuid=user)  # 查找回收站
        folder.parent_folder_id = recycle_bin  # 修改 parent_folder_id
        folder.save()  # 保存更改

        return json_response('', '文件夹已移到回收站', status.HTTP_200_OK)

    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)
    except Folder.DoesNotExist:
        return json_response('', '文件夹不存在', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return json_response('', f'发生错误: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_check(['DELETE'])
@transaction.atomic
def move_file_to_recycle_bin(request):
    # 从请求中获取文件 ID 和用户 ID
    file_id = request.GET.get('file_id')
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')

    # 校验参数是否存在
    if not file_id or not user_id:
        return json_response('', '缺少必要参数', status.HTTP_400_BAD_REQUEST)

    # 验证 UUID 格式
    try:
        user_id = UUID(user_id)
        file_id = UUID(file_id)
    except ValueError:
        return json_response('', '无效的用户 ID 或文件 ID 格式', status.HTTP_400_BAD_REQUEST)

    try:
        # 获取用户和文件
        user = User.objects.get(uuid=user_id)
        file = File.objects.get(file_id=file_id, uuid=user)

        # 查找用户的回收站文件夹
        recycle_bin = Folder.objects.get(name='回收站', uuid=user)

        # 移动文件到回收站：将文件的 parent_folder_id 修改为回收站的 ID
        file.folder_id = recycle_bin
        file.save()  # 保存更改

        return json_response('', '文件已移到回收站', status.HTTP_200_OK)

    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)
    except File.DoesNotExist:
        return json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
    except Folder.DoesNotExist:
        return json_response('', '回收站文件夹不存在', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return json_response('', f'发生错误: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)
