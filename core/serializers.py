from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from rest_framework import serializers

from .models import UserMeta, VerificationGa


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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }


class UserMetaSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserMeta
        exclude = ['id', 'mobile_verified', 'email_verified', 'verification_type', 'status']
        extra_kwargs = {
            'tel': {'required': True},
            'national_id': {'required': True},
            'mobile': {'read_only': True},
            'father_name': {'required': True},
            'birth_date': {'required': True},
            'birth_place': {'required': True},
            'home_address': {'required': True},
            'identity_card_number': {'required': True},
        }

    def update(self, instance, validated_data):
        if not instance.identity_card_image and not validated_data.get('identity_card_image'):
            raise serializers.ValidationError({'identity_card_image': [_("No file was submitted.")]})
        if not instance.national_card_image and not validated_data.get('national_card_image'):
            raise serializers.ValidationError({'national_card_image': [_("No file was submitted.")]})
        user_data = validated_data.get('user')
        first_name = user_data.get('first_name', None)
        last_name = user_data.get('last_name', None)
        email = user_data.get('email', None)
        if first_name:
            instance.user.first_name = first_name
        if last_name:
            instance.user.last_name = last_name
        if email:
            instance.user.email = email
        instance.user.save()
        validated_data.pop('user')

        super(UserMetaSerializer, self).update(instance, validated_data)
        return instance

    def validate_mobile(self, value):
        request = self.context.get('request')
        try:
            user_meta = UserMeta.objects.get(mobile=value)
            if request.user != user_meta.user:
                raise serializers.ValidationError(_("Mobile number is duplicated."))
        except UserMeta.DoesNotExist as e:
            pass
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("email address is duplicated."))
        return value

    def validate_national_id(self, value):
        request = self.context.get('request')
        try:
            user_meta = UserMeta.objects.get(national_id=value)
            if request.user != user_meta.user:
                raise serializers.ValidationError(_("National ID is duplicated."))
        except UserMeta.DoesNotExist as e:
            pass
        return value
