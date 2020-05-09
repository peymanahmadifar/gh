from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import LenderSerializer, MobileSerializer
from .models import Lender
from core.util.permissions import UserRolePermission
from .util.permissions import StaffRolePermission


class LenderViewSet(viewsets.ModelViewSet):
    queryset = Lender.objects.all()
    serializer_class = LenderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        UserRolePermission
    )


class InviteMember(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['mobile'],
            properties={
                'mobile': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def post(self, request, *args, **kwargs):
        serializer = MobileSerializer(data=request.data,
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_200_OK)
