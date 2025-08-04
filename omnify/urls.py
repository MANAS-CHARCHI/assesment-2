
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('USER.urls')),
    path('fitness/', include('omnifyFitness.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
