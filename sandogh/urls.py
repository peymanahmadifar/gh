from django.urls import path, include
from rest_framework import routers, permissions
from . import views
from core import views as core_views

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import pyotp

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        # terms_of_service="https://www.google.com/policies/terms/",
        # contact=openapi.Contact(email="contact@snippets.local"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('get-token/', core_views.MyObtainAuthToken.as_view()),
    path('refresh-token/', core_views.RefreshToken.as_view()),
    path('logout/', core_views.Logout.as_view()),
    path('enable-ga/', core_views.EnableGa.as_view()),
    path('disable-ga/', core_views.DisableGa.as_view()),
    # path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
