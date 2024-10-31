from django.urls import path
from cloud.views.auth import auth_views
from cloud.views.file import file_actions, recycle_bin as file_recycle_bin
from cloud.views.folder import folder_actions, recycle_bin as folder_recycle_bin
from cloud.views.query import query_views
from cloud.views.utils import common_actions

urlpatterns = [
    # 身份验证操作
    path('register', auth_views.register, name='register'),
    path('login', auth_views.login, name='login'),

    # 文件管理操作
    path('file/upload_small_file', file_actions.upload_small_file, name='upload_small_file'),
    path('file/download_small_file', file_actions.download_small_file_content, name='download_small_file'),
    path('file/move_to_recycle_bin', file_recycle_bin.move_file_to_recycle_bin, name='move_file_to_recycle_bin'),

    # 文件夹操作
    path('folder/create', folder_actions.new_folder, name='create_folder'),
    path('folder/move_to_recycle_bin', folder_recycle_bin.move_folder_to_recycle_bin,
         name='move_folder_to_recycle_bin'),

    # 查询操作
    path('user/find', query_views.find_user, name='find_user'),
    path('file/metadata', query_views.get_file_metadata, name='get_file_metadata'),
    path('file/list', query_views.get_filelist, name='get_filelist'),

    # 通用操作
    path('rename', common_actions.rename_item, name='rename_item')
]
