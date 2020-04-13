from django.urls import path, include
from rest_framework import routers
from . import views
from rest_framework.authtoken import views as authView

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    path('api-auth/', authView.obtain_auth_token)
]
