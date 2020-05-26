from random import randrange

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from rest_framework import serializers

from .models import UserMeta, VerificationGa, Confirm, Campaign, LastB, VerificationSms
from .util.extend import CellphoneField, PhoneField
from .util.extra_helper import get_ip


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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    ga_key = serializers.CharField(
        label=_("Google Authentication key"),
        required=False
    )
    sms_key = serializers.CharField(
        label=_("Sms Authentication key"),
        required=False
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        ga_key = attrs.get('ga_key')
        sms_key = attrs.get('sms_key')

        request = self.context.get('request')

        if username and password:
            user = authenticate(request=request, username=username, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if user:
                try:
                    userMeta = user.usermeta
                except UserMeta.DoesNotExist:
                    msg = _('UserMeta does not exist.')
                    raise serializers.ValidationError(msg, code='authorization')
                if userMeta.verification_type == UserMeta.VERIFICATION_GA:
                    if ga_key:
                        try:
                            user_ga = user.verificationga
                        except VerificationGa.DoesNotExist:
                            msg = _('The GA is enabled but your secure key does not exist in the database.')
                            raise serializers.ValidationError(msg, code='authorization')
                        if not user_ga.verify(ga_key):
                            LastB.objects.create(user=user, ip=get_ip(request), type=UserMeta.VERIFICATION_GA)
                            msg = _('Google authentication key is wrong.')
                            raise serializers.ValidationError({'ga_key': [msg]}, code='authorization')
                    else:
                        msg = _('ga_key is required.')
                        raise serializers.ValidationError({'ga_key': [msg]}, code='authorization')
                if userMeta.verification_type == UserMeta.VERIFICATION_SMS:
                    try:
                        user_sms_record = user.verificationsms
                    except VerificationSms.DoesNotExist:
                        user_sms_record = None
                    if user_sms_record and (user_sms_record.created_at + timezone.timedelta(hours=1) < timezone.now()):
                        user_sms_record.delete()
                        user_sms_record = None
                    if sms_key:
                        if not user_sms_record:
                            msg = _('Verification Code was not found.')
                            raise serializers.ValidationError({'sms_key': [msg]}, code='authorization')
                        elif user_sms_record.code != sms_key:
                            LastB.objects.create(user=user, ip=get_ip(request), type=UserMeta.VERIFICATION_SMS)
                            msg = _('The code entered is incorrect.')
                            raise serializers.ValidationError({'sms_key': [msg]}, code='authorization')
                        elif user_sms_record.updated_at + timezone.timedelta(
                                minutes=user_sms_record.lifetime) < timezone.now():
                            msg = _('The code expired.')
                            raise serializers.ValidationError({'sms_key': [msg]}, code='authorization')
                    else:
                        from math import ceil
                        if not user_sms_record:
                            pass
                        elif user_sms_record.update_count >= settings.CUSTOM_AUTHENTICATION['MAX_LOGIN_SMS_PER_HOUR']:
                            timedelta = (user_sms_record.created_at + timezone.timedelta(hours=1)) - timezone.now()
                            minutes = ceil(timedelta.seconds / 60)
                            msg = _('Your attempts are too much. You can try again in {} minutes.'.format(minutes))
                            raise serializers.ValidationError(msg, code='authorization')
                        elif user_sms_record.updated_at + timezone.timedelta(
                                minutes=user_sms_record.lifetime) > timezone.now():
                            timedelta = (user_sms_record.updated_at + timezone.timedelta(
                                minutes=user_sms_record.lifetime)) - timezone.now()
                            msg = _('You cannot request a code until {} seconds later.'.format(timedelta.seconds))
                            raise serializers.ValidationError(msg, code='authorization')
                        VerificationSms.send_new_code(user)
                        mobile = '*******' + user.usermeta.mobile[-4:]
                        msg = _('The verification code was sent to your number {}.'.format(mobile))
                        raise serializers.ValidationError(msg, code='authorization')
            else:
                try:
                    user = User.objects.get(
                        Q(usermeta__mobile=username) | Q(usermeta__national_id=username) | Q(username=username) | Q(
                            email=username))
                    LastB.objects.create(user=user, ip=get_ip(request))
                except (User.DoesNotExist, UserMeta.DoesNotExist)as e:
                    pass
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class UserMetaSerializer(serializers.ModelSerializer):
    mobile = CellphoneField(read_only=True)
    tel = PhoneField(required=True)

    class Meta:
        model = UserMeta
        exclude = ['user']
        extra_kwargs = {
            'id': {'read_only': True},
            'national_id': {'required': True, 'validators': []},
            # 'mobile': {'read_only': True},
            'father_name': {'required': True},
            'birth_date': {'required': True},
            'birth_place': {'required': True},
            'home_address': {'required': True},
            'identity_card_number': {'required': True},
            'status': {'read_only': True},
            'verification_type': {'read_only': True},
            'mobile_verified': {'read_only': True},
            'email_verified': {'read_only': True},
        }

    # def get_fields(self, *args, **kwargs):
    #     fields = super(UserMetaSerializer, self).get_fields(*args, **kwargs)
    #     request = self.context.get('request', None)
    #     if request and getattr(request, 'method', None) == "PUT":
    #         fields['mobile'].read_only = True
    #     if request and getattr(request, 'method', None) == "POST":
    #         fields['mobile'].required = True
    #     return fields

    def update(self, instance, validated_data):
        print(validated_data.get('identity_card_image'))
        if not instance.identity_card_image and not validated_data.get('identity_card_image'):
            raise serializers.ValidationError({'identity_card_image': [_("No file was submitted.")]})
        if not instance.national_card_image and not validated_data.get('national_card_image'):
            raise serializers.ValidationError({'national_card_image': [_("No file was submitted.")]})
        super(UserMetaSerializer, self).update(instance, validated_data)
        return instance

    def validate_mobile(self, value):
        if UserMeta.objects.filter(mobile=value).exclude(id=self.context.get('request').user.usermeta.id).exists():
            raise serializers.ValidationError(_("Mobile number is duplicated."))
        return value

    def validate_national_id(self, value):
        if UserMeta.objects.filter(national_id=value).exclude(id=self.context.get('request').user.usermeta.id).exists():
            raise serializers.ValidationError(_("National ID is duplicated."))
        return value


class UserSerializer(serializers.ModelSerializer):
    usermeta = UserMetaSerializer()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'usermeta']
        extra_kwargs = {
            'id': {'read_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'read_only': True}
        }

    # def create(self, validated_data):
    #     return

    def update(self, instance, validated_data):
        usermeta_serializer = self.fields['usermeta']
        usermeta_instance = instance.usermeta
        usermeta_data = validated_data.pop('usermeta')
        usermeta_serializer.update(usermeta_instance, usermeta_data)
        super(UserSerializer, self).update(instance, validated_data)
        return instance

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(id=self.context.get('request').user.id).exists():
            raise serializers.ValidationError(_("email address is duplicated."))
        return value


class ChangePasswordSerializer(serializers.Serializer):
    password_current = serializers.CharField(label=_('current password'), required=True)
    password = serializers.CharField(label=_('new password'), min_length=4, max_length=20, required=True)
    password_confirm = serializers.CharField(label=_('confirm new password'), required=True)

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['password'])
        user.save()

        return validated_data

    def validate_password_current(self, value):
        data = self.initial_data
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("current password is wrong"))
        return value

    def validate_password_confirm(self, value):
        data = self.initial_data
        if data['password'] != value:
            raise serializers.ValidationError(_("Password confirm is wrong."))
        return value


class ResetPasswordRequestSerializer(serializers.Serializer):
    username = serializers.CharField(label=_('Username'), required=True, max_length=60)
    _user = None

    def create(self, validated_data):
        username = validated_data['username']
        reset_password_request_code(self._user, self._user.usermeta.mobile)
        # @todo if confirmation count exceeds return reasonable error to user to see and pay attention!
        return validated_data

    def validate_username(self, value):
        try:
            # search for number in user model
            user = User.objects.get(
                Q(usermeta__mobile=value) | Q(usermeta__national_id=value) | Q(username=value) | Q(
                    email=value))
            self._user = user
            # if not user.is_active:
            #     raise serializers.ValidationError(_("Username is not active!"))
        except User.DoesNotExist as e:
            raise serializers.ValidationError(_("username does not exist!"))
        return value


class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField(label=_('username'), required=True, max_length=60)
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
            usermeta = u.usermeta
            usermeta.mobile_verified = True
            usermeta.save()
        except UserMeta.DoesNotExist:
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
            confirm = Confirm.objects.get(user__username=data['username'], which=Confirm.WHICH_RESET_PASSWORD)
            self._confirm = confirm
            if confirm.code == value:
                return value
        except Confirm.DoesNotExist:
            pass
        raise serializers.ValidationError(_("Code is wrong!"))
