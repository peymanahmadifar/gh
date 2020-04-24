from rest_framework import views, status
from django.http import HttpResponse
from rest_framework import serializers
from .models import MobileTemp, Download

from django.views.decorators.http import require_GET
from django.contrib.auth.models import User
from .util.extra_helper import get_ip
from .util.auth_helper import auth_token_response
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token

# Create your views here.


from rest_framework import exceptions
from .models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from .util.authentication import get_authorization_header, CustomTokenAuthentication
from django.utils import timezone


class MyObtainAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.get_token(request, user)

        return Response({
            'access_token': token.access_token,
            'refresh_token': token.refresh_token
        })


obtain_auth_token = MyObtainAuthToken.as_view()


class RefreshToken(ObtainAuthToken):

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
        access_token = token.refresh_access_token()
        return Response({
            'access_token': access_token,
        })


refresh_token = RefreshToken.as_view()


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
