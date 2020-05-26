from django.utils import timezone
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import views, status, exceptions, serializers, generics
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from sandogh.models import Member, Staff
from .util.permissions import UserRolePermission
from .util.extra_helper import get_ip
from .util.auth_helper import auth_token_response
from .util.authentication import get_authorization_header, CustomTokenAuthentication
from .models import Token, UserMeta, VerificationGa, MobileTemp, Download, Confirm, VerificationSms
from .serializers import LoginSerializer, ChangePasswordSerializer, ResetPasswordRequestSerializer, \
    ResetPasswordSerializer


class MyObtainAuthToken(ObtainAuthToken):

    @swagger_auto_schema(
        # operation_description="",
        # operation_summary="",
        # request_body=AuthTokenSerializer,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'ga_key': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='It will be required if the user enables the Google Authentication'),
            },
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'access_token_expiration': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh_token_expiration': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'member_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                        type=openapi.TYPE_OBJECT, properties={'member-id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                              'lender-name': openapi.Schema(
                                                                  type=openapi.TYPE_STRING)})),
                    'staff_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                        type=openapi.TYPE_OBJECT, properties={'staff-id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                              'lender-name': openapi.Schema(
                                                                  type=openapi.TYPE_STRING)})),
                },
            ),
            #     status.HTTP_204_NO_CONTENT: openapi.Response(
            #         description="this should not crash (response object with no schema)"
            #     )
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data,
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.get_token(request, user)
        user_status = UserMeta.STATUS_CHOICES[user.usermeta.status][1]
        member_ids = []
        for member in Member.objects.filter(user=user):
            member_ids.append({'member-id': member.id, 'lender-name': member.lender.name})
        staff_ids = []
        for staff in Staff.objects.filter(user=user):
            staff_ids.append({'staff-id': staff.id, 'lender-name': staff.lender.name})
        return Response({
            'access_token': token.access_token,
            'refresh_token': token.refresh_token,
            'access_token_expiration': str(token.access_token_created_at + timezone.timedelta(
                minutes=token.access_token_lifetime)),
            'refresh_token_expiration': str(token.refresh_token_created_at + timezone.timedelta(
                minutes=token.refresh_token_lifetime)),
            'user_status': user_status,
            'member_ids': member_ids,
            'staff_ids': staff_ids,
        })


class RefreshToken(ObtainAuthToken):
    authentication_classes = ()

    @swagger_auto_schema(
        operation_description='It takes refresh_token for authorization',
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                    'access_token_expiration': openapi.Schema(type=openapi.TYPE_STRING, description='datetime'),
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):

        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != CustomTokenAuthentication.keyword.lower().encode():
            msg = _('Refresh token is required.')
            raise exceptions.AuthenticationFailed(msg)

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            refresh_token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = Token.objects.select_related('user').get(refresh_token=refresh_token)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if token.refresh_token_created_at + timezone.timedelta(minutes=token.refresh_token_lifetime) <= timezone.now():
            token.delete()
            raise exceptions.AuthenticationFailed(_('Token expired.'))
        token.refresh_access_token()
        return Response({
            'access_token': token.access_token,
            'access_token_expiration': str(token.access_token_created_at + timezone.timedelta(
                minutes=token.access_token_lifetime)),
        })


class Logout(views.APIView):

    def get(self, request, format=None):
        request.auth.delete()
        return Response(status=status.HTTP_200_OK)


class EnableGaAuth(views.APIView):

    @swagger_auto_schema(
        operation_description='It will return the google authentication url if this already is enabled.',
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'key': openapi.Schema(type=openapi.TYPE_STRING),
                    'url': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        },
    )
    def get(self, request, format=None):
        userMeta = request.user.usermeta
        if userMeta.verification_type == UserMeta.VERIFICATION_SMS:
            return Response({"details": 'You have already enabled Sms authentication.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if userMeta.verification_type == UserMeta.VERIFICATION_GA:
            # raise exceptions.APIException(_('Google Authentication already is enabled.'))
            result = VerificationGa.enable_user_ga(request.user, True)
        else:
            result = VerificationGa.enable_user_ga(request.user)
            userMeta.verification_type = UserMeta.VERIFICATION_GA
            userMeta.save()
        return Response(result, status=status.HTTP_200_OK)


class EnableSmsAuth(views.APIView):

    @swagger_auto_schema(responses={200: ''}, )
    def get(self, request, format=None):
        userMeta = request.user.usermeta
        if userMeta.verification_type == UserMeta.VERIFICATION_GA:
            return Response({"details": 'You have already enabled Google authentication.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if userMeta.verification_type == UserMeta.VERIFICATION_SMS:
            return Response({"details": 'You have already enabled Sms authentication.'},
                            status=status.HTTP_400_BAD_REQUEST)
        userMeta.verification_type = UserMeta.VERIFICATION_SMS
        userMeta.save()
        return Response(status=status.HTTP_200_OK)


class DisableGaAuth(views.APIView):

    def get(self, request, format=None):
        userMeta = request.user.usermeta
        if userMeta.verification_type == UserMeta.VERIFICATION_GA:
            userMeta.verification_type = UserMeta.VERIFICATION_PRIMARY
            userMeta.save()
            VerificationGa.objects.filter(user=request.user).delete()
        else:
            pass
        return Response(status=status.HTTP_200_OK)


class DisableSmsAuth(views.APIView):

    def get(self, request, format=None):
        userMeta = request.user.usermeta
        if userMeta.verification_type == UserMeta.VERIFICATION_SMS:
            userMeta.verification_type = UserMeta.VERIFICATION_PRIMARY
            userMeta.save()
            VerificationSms.objects.filter(user=request.user).delete()
        else:
            pass
        return Response(status=status.HTTP_200_OK)


class DisableTwoStepAuthByStaff(views.APIView):
    permission_classes = [UserRolePermission]

    def get(self, request, user_id=None):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"details": 'User not found.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user.usermeta.verification_type = UserMeta.VERIFICATION_PRIMARY
        user.usermeta.save()
        VerificationGa.objects.filter(user=user).delete()
        VerificationSms.objects.filter(user=user).delete()
        return Response(status=status.HTTP_200_OK)


class VerificationType(views.APIView):
    @swagger_auto_schema(
        operation_description='Possible values ​​in the response : Primary, Google Authentication, Sms',
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'verification_type': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        },
    )
    def get(self, request, format=None):
        userMeta = request.user.usermeta
        verification_type = UserMeta.VERIFICATION_CHOICES[userMeta.verification_type]
        return Response({'verification_type': verification_type}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.CreateAPIView):
    serializer_class = ChangePasswordSerializer


class ResetPasswordRequestView(generics.CreateAPIView):
    permission_classes = ()
    serializer_class = ResetPasswordRequestSerializer


class ResetPasswordCheckCodeView(views.APIView):
    permission_classes = ()

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'code'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'code': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                },
            ),
        },
    )
    def post(self, request):
        username = request.data.get('username', None)
        if not username:
            raise serializers.ValidationError({'username': _('This field is required.')})

        code = request.data.get('code', None)
        if not code:
            raise serializers.ValidationError({'code': _('This field is required.')})

        is_correct = False
        try:
            confirm = Confirm.objects.get(user__username=username, which=Confirm.WHICH_RESET_PASSWORD)
            is_correct = confirm.code == code
        except Confirm.DoesNotExist:
            pass
        if not is_correct:
            raise serializers.ValidationError({'code': 'کد اشتباه است.'})

        return Response({
            "status": True
        })


class ResetPasswordView(generics.CreateAPIView):
    permission_classes = ()
    serializer_class = ResetPasswordSerializer


class LoginWithTokenView(views.APIView):
    permission_classes = ()

    def post(self, request):
        token = request.data.get('token', None)
        id_parted_token = request.data.get('id_parted_token', None)
        # search token
        try:
            if token:
                t = Token.objects.get(key=token)
            else:
                (userid, parted_token) = id_parted_token.split('_')
                if len(parted_token) < 5:
                    # raise Exception('parted_token is too small! must be at least 5 chars!')
                    raise serializers.ValidationError('parted_token is too small! must be at least 5 chars!')
                t = Token.objects.get(user__id=userid, key__startswith=parted_token)
            # t.user
            response = auth_token_response(t)
            return Response(response)
        except Token.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class LoginWithUserHashID(views.APIView):
    permission_classes = ()

    def post(self, request):
        token = request.data.get('token', None)
        # search token
        try:
            t = Token.objects.get(key=token)
            # t.user
            response = auth_token_response(t)
            return Response(response)
        except Token.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class CheckNumberView(views.APIView):
    """
    check mobile number, add it to the model if it does not exist, return status of the user
    active or not active
    """
    permission_classes = ()

    def post(self, request):

        number = request.data.get('number', None)
        # print(request.data, number)
        result = {
            'available': False
        }

        # validate number
        if not number:
            result['error'] = 'number is not valid'
            return Response(result)

        try:
            # search for number in user model
            user = User.objects.get(username=number)
            result['active'] = user.is_active
        except User.DoesNotExist as e:
            result['available'] = True
            # add the number to MobileTemp model
            temp = {
                'number': number,
                'ip': get_ip(request),
            }
            MobileTemp.objects.update_or_create(number=number, defaults=temp)

        # return suitable result
        return Response(result)


@require_GET
def FileDownloadView(request, url):
    response = HttpResponse(charset='utf-8')
    filename = url.split('/').pop()
    response["Content-Disposition"] = "attachment; filename*=UTF-8''%s" % filename
    response["X-Accel-Redirect"] = u"/protected/{0}".format(url)
    download = Download()
    download.ip = get_ip(request)
    download.path = url
    download.save()
    return response
