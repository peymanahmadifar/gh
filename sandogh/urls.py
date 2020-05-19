from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)
router.register('member-list', views.MemberListViewSet, basename='member-list')
router.register('staff-list', views.StaffListViewSet, basename='staff-list')

urlpatterns = [
    path('', include(router.urls)),
    path('invite-member/', views.InviteMember.as_view(), name='invite-member'),
    path('member-form/', views.MemberForm.as_view(), name='member-form'),
    path('verify-user/', views.VerifyUser.as_view(), name='verify-user'),
]
