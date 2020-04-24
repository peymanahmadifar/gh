from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import update_last_login

from core.models import Roles


def auth_token_response(token):
    user = token.user
    response = {
        'token': token.key,
        'username': user.username,
        # 'first_name': user.first_name,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'staff': user.is_staff,
        'customer_id': None,
        'user_id': user.id,
        'roles': [],
    }

    # if not user.is_staff:
    #     try:
    #         # search on customers
    #         customer = Customer.objects.get(user=user)
    #         response['customer_id'] = customer.id
    #         response['roles'] = ['customer']
    #     except Customer.DoesNotExist as e:
    #         pass
    # else:
        # get roles
        # response['roles'] = Roles.get_by_user(user.id)
        # try:
        #     staff = Staff.objects.get(user_id=user.id)
        #     if staff.branch:
        #         response['branch'] = staff.branch.id
        # except:
        #     pass
        #
        # if user.is_superuser:
        #    response['roles'].append('root')

        # check if the user has extension and retrieve his/her properties
        # try:
        #     ext = Ext.objects.get(user=user)
        #     # add ext properties to response
        #     response["ext_password"] = ext.password
        #     response["ext_number"] = ext.ext_number
        # except:
        #     pass

    update_last_login(None, user)

    return response


class MyObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        response = auth_token_response(token)
        # response = {
        #     'token': token.key,
        #     # 'first_name': user.first_name,
        #     'first_name': user.first_name,
        #     'last_name': user.last_name,
        #     'staff': user.is_staff,
        #     'customer_id': None,
        #     'user_id': user.id,
        #     'roles': [],
        # }
        #
        # if not user.is_staff:
        #     try:
        #         # search on customers
        #         customer = Customer.objects.get(user=user)
        #         response['customer_id'] = customer.id
        #         response['roles'] = ['customer']
        #     except Customer.DoesNotExist as e:
        #         pass
        # else:
        #     # get roles
        #     response['roles'] = Roles.get_by_user(user.id)
        #     #
        #     # if user.is_superuser:
        #     #    response['roles'].append('root')
        #
        #     # check if the user has extension and retrieve his/her properties
        #     try:
        #         ext = Ext.objects.get(user=user)
        #         # add ext properties to response
        #         response["ext_password"] = ext.password
        #         response["ext_number"] = ext.ext_number
        #     except:
        #         pass

        # update last login
        # update_last_login(None, user)

        return Response(response)


obtain_auth_token = MyObtainAuthToken.as_view()
