from rest_framework.routers import DefaultRouter

from . import views
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.conf import settings
# default router supports suffix pattern -> request_uri.api or request_uri.json and ...
# router = DefaultRouter()
#
# router.register(r'bills', views.BillViewSet)
# router.register(r'branches', views.BranchViewSet, 'branches')
# router.register(r'staffs', views.StaffViewSet, 'branches')
# router.register(r'descriptions', views.DescriptionViewSet)
# router.register(r'customers', views.CustomerViewSet)

app_name = 'core'

urlpatterns = [
    url(r'^confirm-email/?$', views.ConfirmEmailView, name='confirm-email'),
    url(r'^test-template$', TemplateView.as_view(template_name='core/email-after-confirmation.html'),
        dict(
            request_id='264',
            day_name='سه‌شنبه',
            date='۹۵/۰۱/۰۱',
            time='۱۰-۱۳',
        name='test-template'
        )),
    url(r'^dl/(.*)/$', views.FileDownloadView)
]

router = DefaultRouter()
router.register(r'user-account', views.UserAccountView, 'user-account')
router.register(r'staffs', views.StaffCoreViewSet, 'staffs')
router.register(r'downloads', views.DownloadViewSet, 'downloads')

apipatterns = [
    url(r'^roles$', views.UpdateRolesView.as_view(), name='roles'),
    url(r'^staffs_by_role/(?P<role>[a-zA-Z\-]+)/$', views.StaffsByRoleView.as_view()),
    url(r'^constants$', views.GetConstantsView.as_view(), name='constants'),
    url(r'^check_number$', views.CheckNumberView.as_view(), name='check_number'),
    url(r'^reset_password_request$', views.ResetPasswordRequestView.as_view(), name='reset_password_request'),
    url(r'^reset_password$', views.ResetPasswordView.as_view(), name='reset_password'),
    url(r'^change_password$', views.ChangePasswordView.as_view(), name='change_password'),
    url(r'^register/?$', views.RegistrationView.as_view(), name='register'),
    url(r'^confirm/?$', views.ConfirmMobileView.as_view(), name='confirm'),
    url(r'^request-confirm-email/?$', views.RequestConfirmEmailView.as_view(), name='request-confirm-email'),
    url(r'^manage_constants$', views.ManageConstantsView.as_view(), name='manage-constants'),
    url(r'^login_with_token$', views.LoginWithTokenView.as_view(), name='login-with-token'),
]

# form_router = SimpleRouter()
form_patterns = [
    url(r'^register/?$', views.RegistrationView.as_view(), name='register-form'),
    url(r'^confirm/?$', views.ConfirmMobileView.as_view(), name='confirm-form'),
    # http://localhost:8000/confirm?email=emamirazavi@gmail.com&code=5a425c72-262c-11e6-ac50-08626650b2c8
    url(r'^request_code/?$', views.RequestCodeView.as_view(), name='request_code'),
]
