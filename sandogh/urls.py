from django.urls import path, include
from rest_framework import routers
from . import views
from core.views import obtain_auth_token, refresh_token

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('get-token/', obtain_auth_token),
    path('refresh-token/', refresh_token),
]
