from core.util.acl import add_role, allow, deny, add_resource, is_allowed
from core.models import Role
import logging

logger = logging.getLogger('django')

# roles definitions
ROLE_ROOT = 'root'
ROLE_ADMIN_LOG = 'admin-log'

NO_ROLE = 'no_role'


class UserRolePermission():
    def has_permission(self, request, view):
        if request.user and request.user.id:
            return user_is_allowed(resource=view.__class__.__name__, privilege=request.method.lower(), request=request)
        return False

    def has_object_permission(self, request, view, obj):
        return True


def user_is_allowed(resource, privilege=None, request=None):
    roles = Role.get_by_user(user_id=request.user.id)
    logger.info('is_allowed: resource %s, user %s, roles: %s' % (resource, request.user.id, roles))
    if is_allowed(resource, privilege=None, roles=None):
        logger.info(
            'user %s, resource %s, roles: %s Yes, it is allowed!' % (request.user.id, resource, roles))
        return True
    else:
        logger.info('user %s, resource %s, roles: %s not allowed!' % (request.user.id, resource, roles))
        return False


def user_has_role(role, user_id=None, request=None):
    if request:
        user_id = request.user.id
    if not user_id:
        raise Exception('has_user_role: bad argument')
    roles = Role.get_by_user(user_id=user_id)
    return role in roles


# start to define resources and roles and accesses

# def test():
#     # add roles
#     add_role('kiosk')
#     # add resources
#     add_resource('akbar')
#     allow('kiosk', 'akbar', 'bezan')
#     allow('kiosk', 'akbar')

# *****************************************************************************
# SALES APP ACLS

# list and get ...
# add_resource('SampleViewSet')


# used for customers
# add_resource('OrderDetailsView')
# add_resource('OrderScheduleDeliveryView')

# allow()
add_role(NO_ROLE)
add_role(ROLE_ROOT)

# *********************************************************************************
# allow root to access all of resources
allow('root')

# ********************************************************************************
# sales resources
# allow every staff to access some resources
# allow(resources=[
#     'SampleViewSet',
# ], privileges=[GET])

# allow([ROLE_ROOT], resources=['SampleViewSet'], privileges=[POST, PUT, PATCH, DELETE])

# allow([ROLE_ROOT, ], 'SampleViewSet')
