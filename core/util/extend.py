from json import dumps
import re
from django.contrib import admin
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.encoding import force_text
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType

from rest_framework.fields import DateTimeField, DateField, DecimalField, CharField, empty, ImageField
from .date import greDatetime, datetime as jldatetime, date as jldate
from . import lang
from .extra_helper import get_ip

from rest_framework.serializers import ModelSerializer, ListSerializer
from rest_framework import serializers
from rest_framework import viewsets, authentication, permissions, renderers, generics, pagination

from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from django.contrib.auth.models import update_last_login
# from core.models import Roles
# from core.util import acl
from . import acl
from rest_framework.settings import api_settings

import warnings


class MyBasicAuthentication(authentication.BasicAuthentication):
    def authenticate(self, request):
        result = super(MyBasicAuthentication, self).authenticate(request)

        # update last login
        if (result):
            update_last_login(None, result[0])

        return result


class StaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return True
        # Read permissions are allowed to any request,
        # # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True
        #
        # # Instance must have an attribute named `owner`.
        # return obj.owner == request.user


class TrackOwnerEditPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        ''':type obj TrackModel'''
        if request.method in ('PUT', 'PATCH'):
            return obj.created_by == request.user
        return True


# @see http://www.django-rest-framework.org/api-guide/permissions/
def GenerateModelPermission(model_permissions):
    if type(model_permissions) != list:
        model_permissions = [model_permissions]

    class ModelPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return request.user.has_perms(model_permissions)

    return ModelPermission


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UnlimitedResultsSetPagination(pagination.PageNumberPagination):
    page_size = None
    # page_size_query_param = 'page_size'
    # max_page_size = 100


class BigResultsSetPagination(pagination.PageNumberPagination):
    page_size = 20000
    # page_size_query_param = 'page_size'
    # max_page_size = 100


class MediumResultsSetPagination(pagination.PageNumberPagination):
    page_size = 400


class DefaultsMixin(object):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    authentication_classes = (
        MyBasicAuthentication,
        authentication.TokenAuthentication,
    )
    permission_classes = (
        permissions.DjangoModelPermissions,
        StaffPermission,
        # acl.RolePermission
    )
    paginate_by = 25
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    pagination_class = StandardResultsSetPagination

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                page = self.request.query_params.get('page', None)
                if page is not None:
                    self._paginator = StandardResultsSetPagination()
                else:
                    self._paginator = self.pagination_class()
        return self._paginator


class PointToPointTokenMixin(object):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    authentication_classes = ()
    permission_classes = ()


class MixinStaffPermission(object):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    authentication_classes = (
        MyBasicAuthentication,
        authentication.TokenAuthentication,
    )
    permission_classes = (
        permissions.IsAuthenticated,
        StaffPermission,
    )
    paginate_by = 25
    paginate_by_param = 'page_size'
    max_paginate_by = 100


class LocalIPPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        ip = get_ip(request)
        return re.match('(192.168.|127.0.0.1).*', ip) != None;


class MixinNoModelPermission(object):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    authentication_classes = (
        MyBasicAuthentication,
        authentication.TokenAuthentication,
    )
    permission_classes = (
        permissions.IsAuthenticated,
        StaffPermission,
        # acl.RolePermission
    )
    paginate_by = 25
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    pagination_class = StandardResultsSetPagination


class MixinTrackOwnerEditPermission(MixinNoModelPermission):
    permission_classes = (
        permissions.IsAuthenticated,
        StaffPermission,
        # acl.RolePermission,
        TrackOwnerEditPermission
    )


class DefaultsCustomerMixin(DefaultsMixin):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    permission_classes = (
        # permissions.DjangoModelPermissions,
        # StaffPermission
        permissions.IsAuthenticated,
    )


class TrackModel(models.Model):
    """
    @see
    https://code.djangoproject.com/wiki/CookBookNewformsAdminAndUser
    https://docs.djangoproject.com/en/1.8/topics/db/models/
    http://stackoverflow.com/questions/1477319/in-django-how-do-i-know-the-currently-logged-in-user
    http://www.djangorocks.com/snippets/set-created-updated-datetime-in-your-models.html
    http://stackoverflow.com/questions/25876821/how-to-add-created-by-and-updated-by-user-to-model-py-by-foreign-keys-in-django
    """
    created_by = models.ForeignKey(User, blank=True, null=True, related_name="%(app_label)s_%(class)s_created_by",
                                   editable=False, on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, blank=True, null=True, related_name="%(app_label)s_%(class)s_updated_by",
                                   editable=False, db_index=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, editable=False, db_index=True)
    created_ip = models.GenericIPAddressField(verbose_name=_('آی‌پی سازنده'), default='', blank=True, null=True,
                                              editable=False)
    updated_ip = models.GenericIPAddressField(verbose_name=_('آی‌پی ادیتور'), default='', blank=True, null=True,
                                              editable=False)

    # @see in core/models class named ChangeLog
    _change_log_model = None

    class Meta:
        abstract = True
        # ordering = ['name']

    #
    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    #     # set update and create time and user before saving action.
    #     # print(self.request)
    #     return super(TrackModel, self).save(force_insert=force_insert, force_update=force_update, using=using,
    #                                         update_fields=update_fields)

    def get_change_log_model(self):
        return self._change_log_model

    def set_change_log_user_meta(self, request, save=True):
        if self.get_change_log_model() and request:
            self.get_change_log_model().set_user_meta_by_request(request, save)
            return self.get_change_log_model()
        return None


"""

    if '_items' not in instance.history:
        instance.history['_items'] = []
    _items = instance.history['_items']
    model_diff = diff_models(instance.old_model, instance)
    if model_diff:
        buff = {
            'fields': model_diff
        }
        buff['time'] = timezone.now().isoformat()
        buff['user_id'] = user_id
        buff['ip'] = instance.updated_ip or instance.created_ip
        if user_id:
            user = User.objects.get(id=user_id)
            ''':type user User'''
            buff['user_name'] = user.get_full_name()
            buff['user_username'] = user.username
            # @todo write staff rule
            try:
                if user.is_staff:
                    buff['user_customer'] = 0
                else:
                    buff['user_customer'] = user.customer.id
            except Customer.DoesNotExist:
                buff['user_customer'] = 0
        instance.history['_items'].append(buff)

"""


# @see pakan/util/extra_helper.py
class HistoryAbstract(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    ip = models.GenericIPAddressField(default='', blank=True, null=True, editable=False)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    is_staff = models.BooleanField(default=True)
    user_username = models.CharField(max_length=100, default='')
    user_fullname = models.CharField(max_length=150, default='')
    changed_fields = JSONField(default=dict, verbose_name=_('Changed Fields'))

    @staticmethod
    def diff_models(old, new):
        if not new:
            return {}
        changes = {}
        fields = list(new._meta.fields)
        for f in fields:
            name = f.name
            if name == 'history':
                continue
            oldone = ''
            if oldone:
                oldone = str(getattr(old, name, None))
            newone = str(getattr(new, name, None))
            if oldone != newone:
                changes[name] = [oldone, newone]
        return changes

    def save_differences(self, old, new):
        ''':type new TrackModel'''
        model_diff = HistoryAbstract.diff_models(old, new)
        if model_diff:
            # history = RequestHistory(request=instance)
            if hasattr(new, 'http_request') and new.http_request:
                # user = User.objects.get(id=user_id)
                user = new.http_request.user
                self.user = user
                self.user_fullname = user.get_full_name()
                self.user_username = user.username
                self.is_staff = user.is_staff
                self.ip = get_ip(new.http_request)
            self.changed_fields = model_diff
            self.save()


class TrackModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
            obj.updated_ip = get_ip(request)
        else:
            obj.created_by = request.user
            obj.created_ip = get_ip(request)
        super(TrackModelAdmin, self).save_model(request, obj, form, change)


class TrackModelSerializer(ModelSerializer):
    # @todo if you want override validated_data uncomment and write your own code!
    # def run_validation(self, data=empty):
    #     validated_data = super(self, TrackModelSerializer).run_validation(data=data)
    #
    #     # json_fields
    #     print('in run_validation:', data)
    #     json_fields = {}
    #     for key in data:
    #         if key[:6] == 'JSON__':
    #             (jkey, jvalue) = key[6:].split('__')
    #             if jkey not in json_fields:
    #                 json_fields[jkey] =
    #             print('in data(key):', key)
    #         # JSON__data__item_count
    #     return validated_data

    def save(self, **kwargs):
        ip = get_ip(self.context['request'])
        user = self.context['request'].user
        if self.instance is not None and self.instance.pk:
            kwargs['updated_by'] = user
            kwargs['updated_ip'] = ip
            action = CHANGE
        else:
            kwargs['created_by'] = user
            kwargs['created_ip'] = ip
            action = ADDITION
        instance = super(TrackModelSerializer, self).save(**kwargs)

        # if i'm here therefore i can track an update or a create action!!!
        # catch all needed data by LogEntry
        # @todo a big bug! when we haven't implemented update method and had just create method, always self.instance
        #       is none!
        # think about it and give a solution
        request = self.context['request']
        try:
            object = force_text(instance)
        except:
            object = 'error-on-retrieving'

        # @todo you must limit length of message below! if it has long length don't pass data...
        message = dumps({
            "name": force_text(instance._meta.verbose_name),
            "object": object,
            "data": request.data,
        })
        # message = [
        #     ('%(action)s %(requestdata)s for %(name)s "%(object)s".') % {
        #         "action" : "Changed" if action == CHANGE else "Added",
        #         'requestdata': force_text(request.data),
        #         'name': force_text(instance._meta.verbose_name),
        #         'object': force_text(instance)
        #     }
        # ]

        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(
                instance).pk,
            object_id=instance.pk,
            object_repr=str(instance),
            action_flag=action,
            change_message=message,
        )

        return instance


class TrackModelListSerializer(ListSerializer):
    def save(self, **kwargs):
        kwargs['updated_by'] = self.context['request'].user
        kwargs['updated_ip'] = get_ip(self.context['request'])
        # @todo its better set updated_by and created_by according to each record
        # if self.instance is not None:
        #     kwargs['updated_by'] = self.context['request'].user
        # else:
        #     kwargs['created_by'] = self.context['request'].user
        return super(TrackModelListSerializer, self).save(**kwargs)


class JalaliDateTimeField(DateTimeField):
    def to_internal_value(self, value):
        if not value:
            return None

        if value:
            value = lang.to_english(value)
            value = greDatetime(value)
        # print(value)
        # convert jalali to gregorian
        return super(JalaliDateTimeField, self).to_internal_value(value)

    def to_representation(self, value):
        request = self.context['request'] if 'request' in self.context else None
        formatted = super(JalaliDateTimeField, self).to_representation(value)
        if request and to_bool(request.query_params.get('__gregorian', False)):
            return formatted
        if request and request.query_params.get('__microsecond'):
            return jldatetime(formatted, True)
        else:
            return jldatetime(formatted)


'''
@deprecated use JalaliDateFieldV2 instead
'''


class JalaliDateField(DateField):
    def to_internal_value(self, value):
        if not value:
            return None

        if value:
            value = lang.to_english(value)
            value = greDatetime(value, time=False)
        # convert jalali to gregorian
        return super(JalaliDateField, self).to_internal_value(value)

    def to_representation(self, value):
        formatted = super(JalaliDateField, self).to_representation(value)
        return jldate(formatted)


class JalaliDateFieldV2(DateField):
    def to_internal_value(self, value):
        if value:
            value = lang.to_english(value)
            value = greDatetime(value, time=False)
        # convert jalali to gregorian
        return super(JalaliDateFieldV2, self).to_internal_value(value)

    def to_representation(self, value):
        formatted = super(JalaliDateFieldV2, self).to_representation(value)
        return jldate(formatted)


class CellphoneField(CharField):
    def to_internal_value(self, value):
        value = super(CellphoneField, self).to_internal_value(value)
        value = lang.to_english(value)
        if re.match('^09\d{9}?$', value) is None:
            raise serializers.ValidationError(_("Cellphone not valid! e.g. 09102260226"))
        return value


class PhoneField(CharField):
    def to_internal_value(self, value):
        value = super(PhoneField, self).to_internal_value(value)
        value = lang.to_english(value)

        if re.match('(0\d{10}(p\d{1,4})?|[^0]\d{7})(p\d{1,4})?$', value) is None:
            raise serializers.ValidationError(
                _("Phone number not valid! e.g. 09102260226 or 02188302728 or for number with extension: 88302728p123"))
        return value


class LandLineField(CharField):
    def to_internal_value(self, value):
        value = super(LandLineField, self).to_internal_value(value)
        value = lang.to_english(value)

        # if value[0:2] != '09' or len(value) != 11:
        if re.match('^[^0]\d{7}$', value) is None:
            raise serializers.ValidationError(_("Landline number not valid! e.g. 88302728"))
        return value


class PersianCharField(CharField):
    def to_internal_value(self, value):
        value = super(PersianCharField, self).to_internal_value(value)
        try:
            value = lang.fix_chars(value)
        except:
            pass
        return value


# deprecated this class has many bugs!
class LocalDecimalField(DecimalField):
    def to_representation(self, value):
        value = super(LocalDecimalField, self).to_representation(value)
        return int(value)


def map_iran_fields(serializers, models):
    # dont import these lines! just know type of serializers and models
    # call this method in each models.py
    # from rest_framework import serializers
    # from django.db import models
    serializers.ModelSerializer.serializer_field_mapping[models.DateTimeField] = JalaliDateTimeField
    serializers.ModelSerializer.serializer_field_mapping[models.DateField] = JalaliDateField
    # serializers.ModelSerializer.serializer_field_mapping[models.DecimalField] = LocalDecimalField
    serializers.ModelSerializer.serializer_field_mapping[models.CharField] = PersianCharField


### view extensions ###
class AjaxForm(generics.RetrieveAPIView, generics.CreateAPIView, generics.UpdateAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'ajax_form.html'
    my_options = {
        # "style": (
        #     {"name": "discount_static", "css":{"direction":"ltr"}},
        #     {"name": "tel", "css":{"direction":"ltr"}},
        #     {"name": "tel2", "css":{"direction":"ltr"}},
        #     {"name": "tel3", "css":{"direction":"ltr"}},
        # )
        # "styleByKey": {
        #     "direction": {"value":"ltr", "fields":[
        #         "discount_static", "tel", "tel2", "tel3", "fax", "email"
        #     ]}
        # }
    }

    def retrieve(self, request, *args, **kwargs):
        # print(self.get_object().__dict__)
        try:
            instance = self.get_object()
        except:
            instance = self.get_queryset().model()

        serializer = self.get_serializer(instance)
        return Response({
            'serializer': serializer,
            'instance': instance,
            'json': dumps(self.my_options),
            'verbose_name': self.get_queryset().model._meta.verbose_name
        })


class NoModelAjaxForm(generics.RetrieveAPIView, generics.CreateAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'ajax_inline_form.html'
    authentication_classes = (
        MyBasicAuthentication,
        authentication.TokenAuthentication,
    )
    my_options = {
        # "style": (
        #     {"name": "discount_static", "css":{"direction":"ltr"}},
        #     {"name": "tel", "css":{"direction":"ltr"}},
        #     {"name": "tel2", "css":{"direction":"ltr"}},
        #     {"name": "tel3", "css":{"direction":"ltr"}},
        # )
        # "styleByKey": {
        #     "direction": {"value":"ltr", "fields":[
        #         "discount_static", "tel", "tel2", "tel3", "fax", "email"
        #     ]}
        # }
    }

    def retrieve(self, request, *args, **kwargs):
        # try:
        #     instance = self.get_object()
        # except:
        #     instance = self.get_queryset().model()
        # data = self.get_initial_data()
        if hasattr(self, "get_initial_data"):
            serializer = self.get_serializer(self.get_initial_data(request))
        else:
            serializer = self.get_serializer()

        return Response({
            'serializer': serializer,
            # 'instance': instance,
            'json': dumps(self.my_options),
            # 'verbose_name' : self.get_queryset().model._meta.verbose_name
        })

        # def get_initial_data(self):
        #     return {}


class RetrieveUpdateViewSet(viewsets.mixins.RetrieveModelMixin,
                            viewsets.mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    pass


class RetrieveListUpdateViewSet(viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.UpdateModelMixin,
                                viewsets.mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    pass


class RetrieveUpdateDeleteViewSet(viewsets.mixins.RetrieveModelMixin,
                                  viewsets.mixins.UpdateModelMixin,
                                  viewsets.mixins.DestroyModelMixin,
                                  viewsets.GenericViewSet):
    pass


class CreateRetrieveUpdateDeleteViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.RetrieveModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet):
    pass


class CreateRetrieveListViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.RetrieveModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet):
    pass


class ModelViewSetNoDelete(viewsets.mixins.CreateModelMixin,
                           viewsets.mixins.RetrieveModelMixin,
                           viewsets.mixins.UpdateModelMixin,
                           viewsets.mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    pass


class DownloadViewSet():
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace', 'download']

    def list(self, request, *args, **kwargs):
        if to_bool(request.GET.get('_download_excel', '0')) == 1:
            # call download
            return self.download(request)
        return super(DownloadViewSet, self).list(request, *args, **kwargs)

    def download(self, request):
        from .extra_helper import play_download
        return play_download(self)


def raise_not_field_error(msg):
    raise serializers.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [_(msg)]})


def to_bool(s):
    if type(s) is bool:
        return s
    if type(s) is not str:
        return bool(s)
    if s.lower() in ('true', '1'):
        return True
    elif s.lower() in ('false', '0'):
        return False
    else:
        raise ValueError(
            '%s can not be converted to bool.' % s)  # evil ValueError that doesn't tell you what the wrong value was


def set_creator_props_by_request(model, request, save=False):
    ''':type model TrackModel|dict'''
    if type(model) == dict:
        if request:
            model['created_by'] = request.user
            model['created_ip'] = get_ip(request)
    else:
        if request:
            model.created_by = request.user
            model.created_ip = get_ip(request)
            model.http_request = request
            if save:
                model.save()
    return model


def set_updater_props_by_request(model, request, save=False):
    ''':type model TrackModel|dict'''
    if type(model) == dict:
        if request:
            model['updated_by'] = request.user
            model['updated_ip'] = get_ip(request)
    else:
        if request:
            model.updated_by = request.user
            model.updated_ip = get_ip(request)
            model.http_request = request
            if save:
                model.save()
    return model
