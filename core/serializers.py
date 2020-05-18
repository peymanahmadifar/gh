from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from rest_framework import serializers

from .models import UserMeta, VerificationGa
from .util.extend import CellphoneField, PhoneField


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

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        ga_key = attrs.get('ga_key')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)

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
                            msg = _('The GA is enabled but VerificationGa does not exist.')
                            raise serializers.ValidationError(msg, code='authorization')
                        if not user_ga.verify(ga_key):
                            msg = _('Google authentication key is wrong.')
                            raise serializers.ValidationError(msg, code='authorization')
                    else:
                        msg = _('Must include "ga_key".')
                        raise serializers.ValidationError(msg, code='authorization')

            else:
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
