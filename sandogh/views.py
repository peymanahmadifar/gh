from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.util.extend import StandardResultsSetPagination
from .serializers import LenderSerializer, InviteMemberSerializer, VerifyUserSerializer, MemberSerializer, \
    StaffSerializer, AssignRoleSerializer
from .util.helpers import get_staff
from .util.permissions import StaffRolePermission
from .models import Lender, Member, Staff, Role
from core.util.permissions import UserRolePermission
from core.serializers import UserSerializer
from core.models import UserMeta
from .util.permissions import roles as sandogh_roles


class LenderViewSet(viewsets.ModelViewSet):
    queryset = Lender.objects.all()
    serializer_class = LenderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        UserRolePermission
    )


class InviteMemberView(APIView):
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


class MemberFormView(APIView):

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


class VerifyUserView(APIView):
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


class RolesView(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'roles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                },
            ),
        },
    )
    def get(self, request):
        return Response({"roles": sandogh_roles}, status.HTTP_200_OK)


class StaffsByRoleView(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='role', in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="name of role",
                required=True
            ),
        ],
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                },
            ),
        },
    )
    def get(self, request, role):
        if not role in sandogh_roles:
            return Response({"details": 'Role does not exists'}, status.HTTP_400_BAD_REQUEST)
        staff = get_staff(request)
        staffs = Role.get_staff_by_role(role, staff.lender_id)
        return Response(StaffSerializer(many=True).to_representation(staffs))


class AssignRoleView(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        request_body=AssignRoleSerializer(),
        responses={200: ''}
    )
    def post(self, request, *args, **kwargs):
        serializer = AssignRoleSerializer(data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_200_OK)


class RemoveRoleView(APIView):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffRolePermission
    )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='staff_id', in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                name='role', in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="name of role",
                required=True
            ),
        ],
    )
    def get(self, request, staff_id, role):
        try:
            staff = Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return Response({"details": 'Staff not found.'}, status.HTTP_400_BAD_REQUEST)
        request_staff = get_staff(request)
        if request_staff.lender != staff.lender:
            return Response({"details": 'The staff do not belong to the lender.'}, status.HTTP_400_BAD_REQUEST)
        try:
            staff_role = Role.objects.get(role=role, staff=staff)
        except Role.DoesNotExist:
            return Response({"details": 'Staff role not found.'}, status.HTTP_400_BAD_REQUEST)
        staff_role.delete()
        return Response(status.HTTP_200_OK)
