from django.urls import path
from cloud import upload_views as upload_views
from cloud import user_views as user_views
from cloud_disk_backend import global_function as global_views

urlpatterns = [
    path('upload_file', upload_views.upload_file),
    path('new_folder', upload_views.new_folder),
    path('register',user_views.register),

    path('verify_code',global_views.send_verify_code_email)
]
