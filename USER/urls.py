from django.urls import path
from USER.views import(
    RegisterView,
    LoginView,
    LogoutView,
    UserView,
    CookieTokenRefreshView,
    VerifyUserView,
    ForgetPasswordView,
    ActivateAccountView,
    changeForgetPasswordView,
    UpdateUserView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('profile', UserView.as_view(), name='profile'),
    path('refresh', CookieTokenRefreshView.as_view(), name='refresh-token'),
    path('verify', VerifyUserView.as_view(), name='verify-user'),
    path('update', UpdateUserView.as_view(), name='update-user'),
    path('forget-password', ForgetPasswordView.as_view(), name='forget-password'),
    path('changeforgetpassword/<str:email>/<uuid:token>', changeForgetPasswordView.as_view(), name='change-forget-password'),
    path('activate/<token>', ActivateAccountView.as_view(), name='activate-account'),
]

