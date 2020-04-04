from django.shortcuts import render
from rest_framework import views, generics, viewsets, status
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.views.generic import TemplateView
from django.http import HttpResponse
from rest_framework.response import Response
from django.template.loader import render_to_string
from rest_framework import permissions, serializers
from django.core.exceptions import ValidationError
import json
from core.models import Preferences, Roles, MobileTemp, PrefConstants, Download, Confirm
from .util.extend import (
    DefaultsMixin,
    DefaultsCustomerMixin,
    MixinNoModelPermission,
    StandardResultsSetPagination,
    BigResultsSetPagination,
    StaffPermission,
    AjaxForm)
from .util import extend
from core.util.helper import email_request_code

from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.views.decorators.http import require_GET, require_POST
from core.serializers import (
    RegistrationSerializer,
    ConfirmMobileSerializer,
    RequestCodeSerializer,
    UserAccountSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    StaffSerializer,
    RequestConfirmEmailSerializer,
    DownloadSerializer,
    StaffByRoleSerializer
)
from core.util import acl
from django.contrib.auth.models import User
from core.util.extra_helper import get_ip, play_filtering_form
from core.util.auth_helper import auth_token_response
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token


# Create your views here.


class RegistrationView(generics.RetrieveAPIView, generics.CreateAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    permission_classes = ()
    serializer_class = RegistrationSerializer
    # queryset = Customer.objects.all()

    # my_options = {
    #       "styleByKey": {
    #         "direction": {
    #             "value":"ltr",
    #             "fields":
    #                 ["discount_static", "tel", "tel2", "tel3", "fax", "email"]
    #         }
    #     }
    # }


class ConfirmMobileView(generics.CreateAPIView):
    # renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = ()
    permission_classes = ()
    serializer_class = ConfirmMobileSerializer


class StaffsByRoleView(MixinNoModelPermission, views.APIView):
    def get(self, request, role):
        users = Roles.get_users_by_role(role)
        return Response(StaffByRoleSerializer(many=True).to_representation(users))


class UpdateRolesView(MixinNoModelPermission, views.APIView):
    # renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = ()
    # permission_classes = ()
    # serializer_class = RequestCodeSerializer
    def get(self, request):
        json_str = render_to_string('core/roles.json')
        json_obj = json.loads(json_str)
        return Response(Preferences.get('roles', json_obj))

    def put(self, request):
        # save data to preferences model
        Preferences.set('roles', request.data)
        Roles.extract_and_update_roles(request.data)
        return Response(dict(status='ok', msg='roles saved to preferences'));


class GetConstantsView(MixinNoModelPermission, views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # json_str = render_to_string('core/roles.json')
        # json_obj = json.loads(json_str)
        # return Response(Preferences.get('roles', json_obj));
        res = {
            'acl': {
                'roles': acl.get_roles()
            },
            'holidays': PrefConstants.get_holidays()
        }
        return Response(res)


class MobileConstantsView(views.APIView):
    permission_classes = ()

    def get(self, request):
        # return Response({})
        # return Response({'a':1, 'b':1, 'c':1, 'g':1})
        return Response(PrefConstants.get())


class ManageConstantsView(MixinNoModelPermission, views.APIView):
    # renderer_classes = [JSONRenderer]
    def get(self, request):
        return Response(PrefConstants.get())

    def patch(self, request):
        # save data to preferences model
        constants = PrefConstants.get()
        constants.update(request.data)
        PrefConstants.set(constants)
        return self.get(request)
        # return Response(dict(status='ok', msg='constants saved to preferences'));


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


class ResetPasswordRequestView(generics.CreateAPIView):
    permission_classes = ()
    serializer_class = ResetPasswordRequestSerializer


class ResetPasswordView(generics.CreateAPIView):
    permission_classes = ()
    serializer_class = ResetPasswordSerializer


class ChangePasswordView(generics.CreateAPIView):
    serializer_class = ChangePasswordSerializer


@require_GET
def ConfirmEmailView(request):
    address = request.GET.get('address', None)
    code = request.GET.get('code', None)
    if not address or not code:
        return HttpResponseBadRequest('')

    # check email and code
    try:
        confirm = Confirm.objects.get(user__email=address, which=Confirm.WHICH_EMAIL)
    except Confirm.DoesNotExist as e:
        return HttpResponseBadRequest('<h1>Bad Request</h1>')

    # return HttpResponse(str([confirm.code, code]))
    if confirm.code == code:
        # confirm email
        confirm.user.is_active = True
        confirm.user.customer.email_confirm = True
        confirm.user.save()
        confirm.user.customer.save()
        # remove confirm record and confirm user
        confirm.delete()

        return HttpResponseRedirect('/inbox/?confirmed')
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')


class RequestCodeView(generics.CreateAPIView):
    # renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = ()
    permission_classes = ()
    serializer_class = RequestCodeSerializer


class UserAccountView(MixinNoModelPermission, extend.RetrieveUpdateViewSet):
    """
    Admin must be able to edit username, password and activity status of the user!
    This feature specially will be used to edit old customers' accounts
    """
    queryset = User.objects.all()
    serializer_class = UserAccountSerializer


class StaffCoreViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for listing and CREATING bills."""
    # queryset = User.objects.order_by('id')
    serializer_class = StaffSerializer
    pagination_class = BigResultsSetPagination

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = User.objects.all()
        queryset = queryset.order_by('-id')
        queryset = play_filtering_form(queryset, self.request.query_params)
        queryset = queryset.filter(is_staff=True)
        queryset = queryset.exclude(staff=None)
        return queryset


class DownloadViewSet(DefaultsMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DownloadSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Download.objects.all()
        queryset = queryset.order_by('-id')
        queryset = play_filtering_form(queryset, self.request.query_params)
        return queryset


class RequestConfirmEmailView(DefaultsCustomerMixin, views.APIView):
    def get(self, request):
        serializer = RequestConfirmEmailSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        email = request.user.email
        serializer = RequestConfirmEmailSerializer(data = request.data, instance = request.user)
        serializer.is_valid(True)
        validated_data = serializer.validated_data
        if not validated_data.get('email') and not email:
            raise serializers.ValidationError({'email':_('This field is required.')})
        if validated_data.get('email', email) == email and request.user.customer.email_confirm:
            raise serializers.ValidationError({'email': _('This email address already confirmed!')})
        email = validated_data.get('email', email)

        # update email
        user = request.user
        user.email = email
        user.save()

        # unconfirm
        customer = user.customer
        customer.email_confirm = False
        customer.save()

        # send confirmation email
        camp = email_request_code(user, email)
        data = serializer.data
        data['request_id'] = camp.id
        return Response(data)

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
