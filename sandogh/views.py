from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.util.extend import StandardResultsSetPagination, get_from_header
from .serializers import LenderSerializer, InviteMemberSerializer, VerifyUserSerializer, MemberSerializer, \
    StaffSerializer
from .util.helpers import get_staff
from .util.permissions import StaffRolePermission
from .models import Lender, Member, Staff
from core.util.permissions import UserRolePermission
from core.serializers import UserSerializer
from core.models import UserMeta


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
        serializer = InviteMemberSerializer(data=request.data,
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_200_OK)


class MemberForm(APIView):

    @swagger_auto_schema(request_body=UserSerializer, responses={200: ''})
    def put(self, request, *args, **kwargs):
        instance = request.user
        if instance.usermeta.status == UserMeta.STATUS_VERIFY:
            return Response({"detail": "The user profile cannot be edited."}, status.HTTP_405_METHOD_NOT_ALLOWED)
        serializer = UserSerializer(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        request.user.usermeta.status = UserMeta.STATUS_WAITING_FOR_VERIFY
        request.user.usermeta.save()
        return Response(status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: UserSerializer()})
    def get(self, request, *args, **kwargs):
        serializer = UserSerializer()
        instance = request.user
        return Response({'data': serializer.to_representation(instance=instance)}, status.HTTP_200_OK)


class StaffListViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission,
    )
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(responses={200: StaffSerializer(many=True)})
    def list(self, request):
        staff = get_staff(request)
        queryset = Staff.objects.filter(lender=staff.lender).order_by('-pk')
        serializer = StaffSerializer(queryset, many=True)
        return Response(serializer.data)


class MemberListViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission,
    )
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(responses={200: MemberSerializer(many=True)})
    def list(self, request):
        staff = get_staff(request)
        queryset = Member.objects.filter(lender=staff.lender).order_by('-pk')
        status = self.request.query_params.get('status', None)
        if status is not None:
            queryset = queryset.filter(user__usermeta__status=status)
        serializer = MemberSerializer(queryset, many=True)
        return Response(serializer.data)


class VerifyUser(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        request_body=VerifyUserSerializer(),
        responses={200: ''}
        # description='choices: {2:reject, 3:verify}'
    )
    def post(self, request, *args, **kwargs):
        serializer = VerifyUserSerializer(data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_200_OK)
