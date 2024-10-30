from django.urls import path
from cloud.views import download_views as download_views, upload_views as upload_views, user_views as user_views, \
    get_info_views as get_info_views, delete_views

urlpatterns = [
    path('new_folder', upload_views.new_folder),
    path('register', user_views.register),
    path('login', user_views.login),
    path('find_user', get_info_views.find_user),
    path('get_filelist', get_info_views.get_filelist),
    path('upload_small_file', upload_views.upload_small_file),
    path('file/metadata/', get_info_views.get_file_metadata),
    path('download', download_views.download_small_file_content),
    path('move_folder_to_recycle_bin', delete_views.move_folder_to_recycle_bin),
    path('move_file_to_recycle_bin', delete_views.move_file_to_recycle_bin),
]
