from random import randrange
from rest_framework import serializers

from django.db import models
from rest_framework.authtoken.models import Token
from sales.models import Request, Branch, Customer, Description
from core.models import Confirm, Download, ChangeLog
from sales.serializers import BranchSerializer
from callcenter.models import Campaign
from accounting.models import Invoice, InvoiceDetail
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from pakan.util.lang import to_english, is_persian_alpha
from uuid import uuid1
from core.util.helper import email_request_code

from core.util.extend import TrackModelSerializer, TrackModelListSerializer, map_iran_fields, CellphoneField, raise_not_field_error
from core.util import acl
from pakan.util.customer_helper import parse_customer_data
from rest_framework import serializers
from captcha.fields import CaptchaField

from accounting.helpers import create_or_update_account
from django.conf import settings
from django.contrib.auth.hashers import make_password
from random import randrange
from pakan.util.date import datetime as jldatetime
import re

map_iran_fields(serializers, models)


def cellphone_request_code(user, mobile, voice=False):
    confirm_data = {
        'user': user,
        'which': Confirm.WHICH_MOBILE,
        'code': randrange(1000, 9999)
    }
    confirm, confirm_created = Confirm.objects.update_or_create(user=user, which=Confirm.WHICH_MOBILE,
                                                                defaults=confirm_data)
    confirm.count += 1
    confirm.save()

    if confirm.count <= 10:
        # @todo remove activation-mobile.html and use messages in django.po
        if voice:
            Campaign.send_voice_captcha(to=mobile, target_user=user, code=confirm.code)
        else:
            Campaign.send_sms(gtw=Campaign.GTW_PARSA_TEMPLATE_SMS, to=mobile, target_user=user, tpl='activationCodeSms',
                              context=dict(type=1, param1=confirm.code))
    else:
        # limit user or ...
        # this behaviour is malicious.
        pass


def reset_password_request_code(user, mobile):
    confirm_data = {
        'user': user,
        'which': Confirm.WHICH_RESET_PASSWORD,
        'code': str(randrange(12222, 99999)),
    }
    confirm, confirm_created = Confirm.objects.update_or_create(user=user, which=Confirm.WHICH_RESET_PASSWORD,
                                                                defaults=confirm_data)
    confirm.count += 1
    confirm.save()

    if confirm.count <= 10:
        # @todo remove activation-mobile.html and use messages in django.po
        Campaign.send_sms(
            gtw=Campaign.GTW_PARSA_TEMPLATE_SMS,
            to=mobile,
            target_user=user,
            tpl='resetPasswordRequestSms',
            context=dict(
                param1=confirm.code
            ))
    else:
        # limit user or ...
        # this behaviour is malicious.
        # reset it by time
        pass


# serializer to register new user
# @see https://github.com/tomchristie/django-rest-framework/issues/951
class RegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=40, label=_('First Name'), required=False)
    last_name = serializers.CharField(max_length=40, label=_('Last Name'), required=False)
    # full_name = serializers.CharField(max_length=40, label=_('Full Name'))
    tel = CellphoneField(label=_('Cellphone'), required=True)
    password = serializers.CharField(label=_('password'), min_length=4, max_length=20, style={'input_type': 'password'},
                                     required=True)
    password_confirm = serializers.CharField(
        label=_('password confirm'), max_length=128, style={'input_type': 'password'})
    email = serializers.EmailField(label=_('email address'), required=False)
    no_cellphone_request = serializers.BooleanField(required=False, write_only=True, default=False)
    voice = serializers.BooleanField(required=False, write_only=True, default=False)

    # agreement = serializers.CharField(max_length=2, label=_('Agreement'), default='off')
    def create(self, validated_data):
        # do all works to register user
        # add or update user
        user_data = {
            'username': validated_data.get('tel', ''),
            'is_active': False,
        }
        if validated_data.get('first_name', None):
            user_data['first_name'] = validated_data.get('first_name')
        if validated_data.get('last_name', None):
            user_data['last_name'] = validated_data.get('last_name')
        if validated_data.get('email', None):
            user_data['email'] = validated_data.get('email')
        user, user_created = User.objects.update_or_create(username=validated_data['tel'], defaults=user_data)

        user.set_password(validated_data.get('password'))
        user.save()

        # add customer
        customer_data = {
            # 'first_name': user_data['first_name'],
            # 'last_name': user_data['last_name'],
            # 'email': user_data['email'],
            'mobile': validated_data.get('tel', ''),
            # 'user': user
        }
        registration_gateway = int(self.context.get('request').META.get('HTTP_GATEWAY_ID', 0))
        if registration_gateway:
            customer_data['registration_gateway'] = registration_gateway

        customer, customer_created = Customer.objects.update_or_create(user=user, defaults=customer_data)

        voice = validated_data.get('voice', False)
        if not validated_data.get('no_cellphone_request', False):
            cellphone_request_code(user, validated_data['tel'], voice)

        if 'email' in validated_data:
            email_request_code(user, validated_data['email'])

        # send telegram message to agents
        msg = _('NEW_CUSTOMER_REGISTERED').format(
            full_name=user.get_full_name() if user.get_full_name() else '',
            customer_id=customer.id,
            created_at=jldatetime(customer.updated_at),
            registration_gateway=customer.get_registration_gateway()
        )
        Campaign.send_telegram_message(to_role=acl.ROLE_AGENT, message=msg)

        return validated_data

    def validate_password_confirm(self, value):
        data = self.initial_data
        if data['password'] != value:
            raise serializers.ValidationError(_("Password confirm is wrong."))
        return value

    def validate_tel(self, value):
        try:
            user = User.objects.get(username=value)
            # comment line below for production
            if user.is_active:
                raise serializers.ValidationError(_("Cellphone number is duplicated."))

            if not user.customer.is_active:
                raise_not_field_error('امکان ثبت نام وجود ندارد. حساب مشتری غیرفعال است.')
        except User.DoesNotExist as e:
            pass
        except Customer.DoesNotExist as e:
            pass
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("email address is duplicated."))
        return value


class UserAccountSerializer(TrackModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'is_active',
        )

    def validate_password(self, value):
        return make_password(value)

    def to_representation(self, instance):
        data = super(UserAccountSerializer, self).to_representation(instance)
        del data['password']
        return data


def _validate_mobile(value):
    try:
        customer = Customer.objects.get(user__username=value)
        if customer.mobile_confirm:
            raise serializers.ValidationError(_("Cellphone number already is confirmed."))
    except Customer.DoesNotExist as e:
        # @todo prevent attacks and make limitations...
        raise serializers.ValidationError(_("Cellphone number does not exist."))
    return customer


#
# class ConfirmEmailSerializer(serializers.Serializer):
#     address = serializers.EmailField(label=_('Cellphone'))
#     code = serializers.CharField(label=_('code'))
#
#     def create(self, validated_data):
#         # every thing is okay! just activate the user and set mobile confirmed true in customer profile
#         customer = Customer.objects.get(user__username=validated_data['mobile'])
#         customer.mobile_confirm = True
#         customer.user.is_active = True
#         customer.save()
#         customer.user.save()
#
#         # create an account for user
#         # create_or_update_account(customer.user)
#
#         return validated_data
#
#     def validate_code(self, value):
#         try:
#             value = to_english(value)
#             confirm = Confirm.objects.get(user__username=self.initial_data['mobile'], which=Confirm.WHICH_MOBILE)
#             if confirm.code == value:
#                 # remove confirm record and confirm user
#                 confirm.delete()
#             else:
#                 raise serializers.ValidationError(_("Code is wrong!"))
#         except Confirm.DoesNotExist as e:
#             pass
#
#         return value


def activate_user_by_cellphone_number(mobile):
    """

    :param mobile: is registered user with customer id that has not been activated yet.
    :type mobile: string
    :return: return Customer
    """
    customer = Customer.objects.get(user__username=mobile)
    confirmed = customer.mobile_confirm
    customer.mobile_confirm = True
    customer.user.is_active = True
    customer.save()
    customer.user.save()

    # send sms about activated account
    if not confirmed:
        Campaign.send_sms(gtw=Campaign.GTW_PARSA_TEMPLATE_SMS, to=mobile,
                          target_user=customer.user,
                          tpl='activatedSms',
                          context=dict(
                              param1=str(mobile),
                              param2=str(customer.id)
                          ))

    return customer


# serializer to confirm mobile phone
class ConfirmMobileSerializer(serializers.Serializer):
    mobile = CellphoneField(label=_('Cellphone'))
    code = serializers.CharField(label=_('کد'))

    def create(self, validated_data):
        # every thing is okay! just activate the user and set mobile confirmed true in customer profile
        activate_user_by_cellphone_number(validated_data['mobile'])

        return validated_data

    def validate_code(self, value):
        try:
            value = to_english(value)
            confirm = Confirm.objects.get(user__username=self.initial_data['mobile'], which=Confirm.WHICH_MOBILE)
            if confirm.code == value:
                # remove confirm record and confirm user
                confirm.delete()
            else:
                raise serializers.ValidationError(_("Code is wrong!"))
        except Confirm.DoesNotExist as e:
            pass

        return value


class RequestCodeSerializer(serializers.Serializer):
    mobile = CellphoneField(label=_('Cellphone'))

    def create(self, validated_data):
        # do all works to confirm user's mobile phone
        # print(validated_data)
        mobile = validated_data['mobile']
        user = User.objects.get(username=mobile)

        try:
            if not user.customer.is_active:
                raise_not_field_error('امکان درخواست کد نیست. حساب مشتری غیرفعال است.')
        except Customer.DoesNotExist as e:
            pass

        cellphone_request_code(user, mobile)

        return validated_data

    def validate_mobile(self, value):
        _validate_mobile(value)
        return value
        # try:
        #     customer = Customer.objects.get(user__username=value)
        #     if customer.mobile_confirm:
        #         raise serializers.ValidationError(_("Cellphone number already is confirmed."))
        # except Customer.DoesNotExist as e:
        #     # @todo prevent attacks and make limitations...
        #     raise serializers.ValidationError(_("Cellphone number does not exist."))
        # return value


class ResetPasswordRequestSerializer(serializers.Serializer):
    username = CellphoneField(label=_('Username'), required=True)
    _user = None

    def create(self, validated_data):
        username = validated_data['username']
        reset_password_request_code(self._user, username)
        # @todo if confirmation count exceeds return reasonable error to user to see and pay attention!
        return validated_data

    def validate_username(self, value):
        try:
            # search for number in user model
            user = User.objects.get(username=value)
            self._user = user
            # if not user.is_active:
            #     raise serializers.ValidationError(_("Username is not active!"))
        except User.DoesNotExist as e:
            raise serializers.ValidationError(_("cellphone/username does not exist!"))
        return value


class ResetPasswordSerializer(serializers.Serializer):
    username = CellphoneField(label=_('username'), required=True)
    code = serializers.CharField(label=_('code'), required=True, max_length=5)
    password = serializers.CharField(label=_('password'), min_length=4, max_length=20, required=True)
    password_confirm = serializers.CharField(label=_('confirm password'), required=True)
    _confirm = None

    def create(self, validated_data):
        u = User.objects.get(username=validated_data['username'])
        ''':type u: User'''
        u.set_password(validated_data['password'])
        u.is_active = True
        try:
            c = u.customer
            c.mobile_confirm = True
            c.save()
        except Customer.DoesNotExist:
            pass
        u.save()

        # delete confirm
        self._confirm.delete()

        return validated_data

    def validate_password_confirm(self, value):
        data = self.initial_data
        if data['password'] != value:
            raise serializers.ValidationError(_("Password confirm is wrong."))
        return value

    def validate_code(self, value):
        data = self.initial_data
        try:
            c = Confirm.objects.get(user__username=data['username'], which=Confirm.WHICH_RESET_PASSWORD)
            self._confirm = c
            if c.code == value:
                return value
        except Confirm.DoesNotExist:
            pass
        raise serializers.ValidationError(_("Code is wrong!"))


class ChangePasswordSerializer(serializers.Serializer):
    password_current = serializers.CharField(label=_('current password'), required=True)
    password = serializers.CharField(label=_('new password'), min_length=4, max_length=20, required=True)
    password_confirm = serializers.CharField(label=_('confirm new password'), required=True)

    def create(self, validated_data):
        u = self.context['request'].user
        ''':type u: User'''
        u.set_password(validated_data['password'])
        u.save()

        return validated_data

    def validate_password_current(self, value):
        data = self.initial_data
        ''':type u: User'''
        u = self.context['request'].user
        if not u.check_password(value):
            raise serializers.ValidationError(_("current password is wrong"))
        return value

    def validate_password_confirm(self, value):
        data = self.initial_data
        if data['password'] != value:
            raise serializers.ValidationError(_("Password confirm is wrong."))
        return value


class DownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Download
        fields = '__all__'


class ChangelogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeLog
        fields = '__all__'


class StaffByRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'id')


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'id', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_blank': True},
            'last_name': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        password = validated_data.get('password', None)
        validated_data['is_staff'] = True
        validated_data['is_active'] = True
        instance = super(StaffSerializer, self).create(validated_data)
        ''':type instance User'''
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def validate_first_name(self, value):
        if not is_persian_alpha(value):
            raise serializers.ValidationError(_("نام باید از حروف فارسی باشد"))
        return value

    def validate_last_name(self, value):
        if not is_persian_alpha(value):
            raise serializers.ValidationError(_("نام خانوادگی باید از حروف فارسی باشد"))
        return value

    def update(self, instance, validated_data):
        # update password
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
            validated_data.pop('password')

        super(StaffSerializer, self).update(instance, validated_data)
        return instance

    def to_representation(self, instance):

        # make sure the user has token to authenticate with api
        Token.objects.get_or_create(user=instance)

        data = super(StaffSerializer, self).to_representation(instance)

        # append token to represented data
        data['token'] = instance.auth_token.key
        return data


class RequestConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=False, required=False)

    def validate_email(self, value):
        filter = User.objects.filter(email=value)
        if self.instance:
            filter = filter.exclude(id=self.instance.id)
        if filter.exists():
            raise serializers.ValidationError(_("email address is duplicated."))
        return value


class SendEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=False, required=True)
    name = serializers.CharField(max_length=100, allow_blank=False, required=True)
    body = serializers.CharField(max_length=1024, allow_blank=False, required=True)
