from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('get-token/', views.MyObtainAuthToken.as_view(), name='get-token'),
    path('refresh-token/', views.RefreshToken.as_view(), name='refresh-token'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('enable-ga/', views.EnableGa.as_view(), name='enable-ga'),
    path('disable-ga/', views.DisableGa.as_view(), name='disable-ga'),
    path('get-verification-type/', views.VerificationType.as_view(), name='get-verification-type'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('reset-password-request/', views.ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('reset-password-check-code/', views.ResetPasswordCheckCodeView.as_view(), name='reset-password-check-code'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
]
