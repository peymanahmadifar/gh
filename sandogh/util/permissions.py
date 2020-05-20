from core.util.acl import add_role, allow, deny, add_resource, is_allowed
from sandogh.models import Role, Staff
import logging

from sandogh.util.helpers import get_staff, get_from_header

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
    staff = get_staff(request)
    if staff.user != request.user:
        raise Exception('The staff-id does not match the logged in user')
    roles = Role.get_by_staff(staff_id=staff.id)
    logger.info('is_allowed: resource %s, staff %s, roles: %s' % (resource, staff.id, roles))
    if is_allowed(resource, privilege, roles):
        logger.info(
            'staff %s, resource %s, roles: %s Yes, it is allowed!' % (staff.id, resource, roles))
        return True
    else:
        logger.info(
            'staff %s, resource %s, roles: %s not allowed!' % (staff.id, resource, roles))
        return False


def staff_has_role(role, staff_id=None, request=None):
    if request:
        staff_id = get_from_header('staff-id', request)
    if not staff_id:
        raise Exception('staff_has_role: bad argument')
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

add_resource('MemberListViewSet')
add_resource('VerifyUserView')
add_resource('StaffListViewSet')
add_resource('RolesView')
add_resource('StaffsByRoleView')
add_resource('AssignRoleView')
add_resource('RemoveRoleView')

# *********************************************************************************
# allow root to access all of resources

allow(ROLE_SANDOGH_ROOT)

allow([ROLE_SANDOGH_OPERATOR], ['MemberListViewSet', 'VerifyUserView'])
allow([ROLE_SANDOGH_ROOT], ['StaffListViewSet'])

# ********************************************************************************
# sales resources
# allow every staff to access some resources
# allow(resources=[
#     'SampleViewSet',
# ], privileges=[GET])
# allow([ROLE_ROOT], resources=['SampleViewSet'], privileges=[POST, PUT, PATCH, DELETE])
# allow([ROLE_ROOT, ], 'SampleViewSet')
