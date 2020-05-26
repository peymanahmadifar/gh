"""
Provides various authentication policies.
"""
from django.contrib.auth.models import User
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import BaseAuthentication


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, str):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


class CustomBackend():
    """
    Use the email and mobile as usernames, if exists.
    """

    def authenticate(self, request, username=None, password=None):

        if username and password:
            user = None
            try:
                user = User.objects.get(Q(username=username) | Q(email=username) |
                                        Q(usermeta__mobile=username) | Q(usermeta__national_id=username))
            except User.DoesNotExist:
                pass
            if user and user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None


class CustomTokenAuthentication(BaseAuthentication):
    """
    Authentication with two tokens : access token and refresh token
    The Access token has a short lifetime than the refresh token.
    Basically, refresh tokens are used to get new access token.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'Token'
    model = None

    def get_model(self):
        if self.model is not None:
            return self.model
        from core.models import Token
        return Token

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(access_token=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if token.access_token_created_at + timezone.timedelta(minutes=token.access_token_lifetime) <= timezone.now():
            raise exceptions.AuthenticationFailed(_('Token expired.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (token.user, token)

    def authenticate_header(self, request):
        return self.keyword
