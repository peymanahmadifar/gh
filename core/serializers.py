from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

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
