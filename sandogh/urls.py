from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)
router.register('member-list', views.MemberListViewSet, basename='member-list')
router.register('staff-list', views.StaffListViewSet, basename='staff-list')

urlpatterns = [
    path('', include(router.urls)),
    path('invite-member/', views.InviteMemberView.as_view(), name='invite-member'),
    path('member-form/', views.MemberFormView.as_view(), name='member-form'),
    path('verify-user/', views.VerifyUserView.as_view(), name='verify-user'),
    path('roles/', views.RolesView.as_view(), name='roles'),
    path('staffs-by-role/<str:role>/', views.StaffsByRoleView.as_view(), name='staff-by-role'),
    path('assign-role/', views.AssignRoleView.as_view(), name='assign-role'),
    path('remove-role/<int:staff_id>/<str:role>/', views.RemoveRoleView.as_view(), name='remove-role'),
]
