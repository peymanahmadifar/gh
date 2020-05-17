from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('lenders', views.LenderViewSet)
router.register('member-list', views.MemberListViewSet, basename='member-list')

urlpatterns = [
    path('', include(router.urls)),
    path('invite-member/', views.InviteMember.as_view()),
    path('member-form/', views.MemberForm.as_view()),
]
