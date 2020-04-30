from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('get-token/', views.MyObtainAuthToken.as_view()),
    path('refresh-token/', views.RefreshToken.as_view()),
    path('logout/', views.Logout.as_view()),
    path('enable-ga/', views.EnableGa.as_view()),
    path('disable-ga/', views.DisableGa.as_view()),
]
