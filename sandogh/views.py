from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import LenderSerializer
from .models import Lender
from core.util.permissions import UserRolePermission


class LenderViewSet(viewsets.ModelViewSet):
    queryset = Lender.objects.all()
    serializer_class = LenderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        UserRolePermission
    )
