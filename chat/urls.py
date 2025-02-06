from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import login_user,signup,get_messages,send_message,get_user_details,index

urlpatterns = [
    path('', index, name='index'),
    path("login",login_user),
    path("signup",signup),
    path("send_message",send_message),
    path("message",get_messages),
    path("user",get_user_details),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)