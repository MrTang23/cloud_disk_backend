from django.urls import path
from cloud import upload_views as upload_views
from cloud import user_views as user_views

urlpatterns = [
    path('upload_file', upload_views.upload_file),
    path('new_folder', upload_views.new_folder),
    path('register', user_views.register),
    path('login', user_views.login),
    path('get_filelist', upload_views.get_filelist),
    path('download', upload_views.download),
    path('upload_folder', upload_views.upload_folder)
]
