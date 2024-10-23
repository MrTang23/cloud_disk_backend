from django.urls import path
from cloud import upload_views as upload_views
from cloud import user_views as user_views
from cloud import download_views as download_views

urlpatterns = [
    path('new_folder', upload_views.new_folder),
    path('register', user_views.register),
    path('login', user_views.login),
    path('find_user', user_views.find_user),
    path('get_filelist', upload_views.get_filelist),
    path('upload_small_file', upload_views.upload_small_file),
    path('download_file', download_views.download_file),
]
