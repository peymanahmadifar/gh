from core.util.acl import add_role, allow, deny, add_resource, is_allowed
from core.util.extend import get_from_header
from sandogh.models import Role, Staff
import logging

logger = logging.getLogger('django')

# roles definitions
ROLE_SANDOGH_ROOT = 'sandogh_root'
ROLE_SANDOGH_OPERATOR = 'sandogh_operator'

NO_ROLE = 'no_role'

roles = [
    ROLE_SANDOGH_ROOT,
    ROLE_SANDOGH_OPERATOR,
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
    staff_id = get_from_header('Staff-Id', request)
    try:
        staff = Staff.objects.get(pk=staff_id)
    except Staff.DoesNotExist:
        raise Exception('Staff does not exist')
    if staff.user != request.user:
        raise Exception('The Staff-Id does not match the logged in user')
    roles = Role.get_by_staff(staff_id=request.headers.get('Staff-Id'))
    logger.info('is_allowed: resource %s, staff %s, roles: %s' % (resource, request.headers.get('Staff-Id'), roles))
    if is_allowed(resource, privilege, roles):
        logger.info(
            'staff %s, resource %s, roles: %s Yes, it is allowed!' % (request.headers.get('Staf-_Id'), resource, roles))
        return True
    else:
        logger.info(
            'staff %s, resource %s, roles: %s not allowed!' % (request.headers.get('Staff-Id'), resource, roles))
        return False


def staff_has_role(role, staff_id=None, request=None):
    if request:
        staff_id = request.headers.get('Staff-Id')
    if not staff_id:
        raise Exception('has_staff_role: bad argument')
    roles = Role.get_by_staff(staff_id=staff_id)
    return role in roles


add_resource('InviteMember')

allow([ROLE_SANDOGH_ROOT], ['InviteMember'])

# start to define resources and roles and accesses

# def test():
#     # add roles
#     add_role('kiosk')
#     # add resources
#     add_resource('akbar')
#     allow('kiosk', 'akbar', 'bezan')
#     allow('kiosk', 'akbar')

# list and get ...
# add_resource('SampleViewSet')

add_resource('MemberListViewSet')
add_resource('VerifyUser')

# *********************************************************************************
# allow root to access all of resources
# allow('root')

allow([ROLE_SANDOGH_OPERATOR], ['MemberListViewSet', 'VerifyUser'])

# ********************************************************************************
# sales resources
# allow every staff to access some resources
# allow(resources=[
#     'SampleViewSet',
# ], privileges=[GET])
# allow([ROLE_ROOT], resources=['SampleViewSet'], privileges=[POST, PUT, PATCH, DELETE])
# allow([ROLE_ROOT, ], 'SampleViewSet')
