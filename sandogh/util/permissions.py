from core.util.acl import add_role, allow, deny, add_resource, is_allowed
from sandogh.models import Role
import logging

logger = logging.getLogger('django')

# roles definitions
ROLE_S_ROOT = 's_root'
# ROLE_ADMIN_LOG = 'admin-log'

NO_ROLE = 'no_role'

roles = [
    ROLE_S_ROOT,
    NO_ROLE,
]

add_role(roles)


class StaffRolePermission():
    def has_permission(self, request, view):
        if request.user and request.user.id:
            return staff_is_allowed(resource=view.__class__.__name__, privilege=request.method.lower(), request=request)
        return False

    def has_object_permission(self, request, view, obj):
        return True


def staff_is_allowed(resource, privilege=None, request=None):
    if not request.headers.get('Staff_Id'):
        raise Exception('The Staff-Id must be sent in the request header')
    roles = Role.get_by_staff(staff_id=request.headers.get('Staff_Id'))
    logger.info('is_allowed: resource %s, staff %s, roles: %s' % (resource, request.headers.get('Staff_Id'), roles))
    if is_allowed(resource, privilege, roles):
        logger.info(
            'staff %s, resource %s, roles: %s Yes, it is allowed!' % (request.headers.get('Staff_Id'), resource, roles))
        return True
    else:
        logger.info(
            'staff %s, resource %s, roles: %s not allowed!' % (request.headers.get('Staff_Id'), resource, roles))
        return False


def staff_has_role(role, staff_id=None, request=None):
    if request:
        staff_id = request.headers.get('Staff_Id')
    if not staff_id:
        raise Exception('has_staff_role: bad argument')
    roles = Role.get_by_staff(staff_id=staff_id)
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


# *********************************************************************************
# allow root to access all of resources
# allow('root')

# ********************************************************************************
# sales resources
# allow every staff to access some resources
# allow(resources=[
#     'SampleViewSet',
# ], privileges=[GET])

# allow([ROLE_ROOT], resources=['SampleViewSet'], privileges=[POST, PUT, PATCH, DELETE])

# allow([ROLE_ROOT, ], 'SampleViewSet')
