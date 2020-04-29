from django.urls import path

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from . import views

app_name = 'core'

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

urlpatterns = [
    path('get-token/', views.MyObtainAuthToken.as_view()),
    path('refresh-token/', views.RefreshToken.as_view()),
    path('logout/', views.Logout.as_view()),
    path('enable-ga/', views.EnableGa.as_view()),
    path('disable-ga/', views.DisableGa.as_view()),
    # path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
