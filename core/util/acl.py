import logging

logger = logging.getLogger('django')

ROLE_TEST = None
# ROLE_TEST = 'crm'
# ROLE_TEST = 'kiosk'

# private variables
resources = []
roles = []
permissions = {}

# roles definitions
ROLE_ROOT = 'root'
ROLE_ADMIN_LOG = 'admin-log'

NO_ROLE = 'no_role'

# request methods
GET = 'get'
PUT = 'put'
PATCH = 'patch'
POST = 'post'
DELETE = 'delete'
DOWNLOAD = 'download'

# all privileges come here!
PRIVILEGE_INVOICE_EDIT = 'invoice-edit'


class RolePermission():
    def has_permission(self, request, view):
        if request.user and request.user.id:
            return is_allowed(resource=view.__class__.__name__, privilege=request.method.lower(), request=request)
        return False

    def has_object_permission(self, request, view, obj):
        return True


# def GenerateRolePermission(roles):
#     if type(roles) !=list:
#         roles = [roles]
#
#     class MyRolePermission():
#         def has_permission(self, request, view):
#             if request.user and request.user.id:
#                 return has_user_role()
#                 # is_allowed(resource=view.__class__.__name__, request=request)
#             return False
#
#         def has_object_permission(self, request, view, obj):
#             return True
#
#     return MyRolePermission


def is_allowed(resource, privilege=None, roles=None, request=None):
    from core.models import Roles

    # return false if the resource id does not exist.
    if not _has_resource(resource):
        raise Exception('resource %s does not exist! add it to core/util/acl.py' % resource)

    if ROLE_TEST:
        roles = [ROLE_TEST]

    if not roles:
        roles = Roles.get_by_user(user_id=request.user.id)

    logger.info('is_allowed: resource %s, user %s, roles: %s' % (resource, request.user.id, roles))

    if resource in permissions:
        for role in roles:
            if not _has_role(role):
                raise Exception('role %s does not exist!' % role)
            if role in permissions[resource]:
                if not privilege or not permissions[resource][role]['privileges'] or privilege in \
                        permissions[resource][role]['privileges']:
                    logger.info(
                        'user %s, resource %s, roles: %s Yes, it is allowed!' % (request.user.id, resource, roles))
                    return True
        logger.info('user %s, resource %s, roles: %s not allowed!' % (request.user.id, resource, roles))
        return False

    return False


def _has_resource(resource):
    return resource in resources


def _has_role(role):
    return role in roles


def get_resources():
    return resources


def get_roles():
    return roles


def get_permissions():
    return permissions


def add_role(id):
    global roles
    roles.append(id)


def add_resource(id):
    global resources
    resources.append(id)


# private method definition
def allow_or_deny(method, roles=None, resources=None, privileges=None):
    if not roles:
        roles = get_roles()
    else:
        roles = [roles] if type(roles) == str else roles

    if not resources:
        resources = get_resources()

    if not privileges:
        privileges = []

    resources = [resources] if type(resources) == str else resources
    privileges = [privileges] if type(privileges) == str else privileges

    for resource in resources:
        if not _has_resource(resource):
            raise Exception('resource %s does not exist! add it to core/util/acl.py' % resource)

        if resource not in permissions:
            permissions[resource] = {}

        for role in roles:
            if not _has_role(role):
                raise Exception('role %s does not exist!' % role)

            if method == 'deny':
                if role in permissions[resource]:
                    if not privileges:
                        del permissions[resource][role]
                    else:
                        permissions[resource][role]['privileges'] = \
                            list(set(permissions[resource][role]['privileges']) - set(privileges))
            else:
                if role not in permissions[resource]:
                    permissions[resource][role] = {
                        'privileges': []
                    }
                permissions[resource][role]['privileges'] = \
                    list(set(permissions[resource][role]['privileges']) | set(privileges))


def allow(roles=None, resources=None, privileges=None):
    allow_or_deny('allow', roles, resources, privileges)


def deny(roles=None, resources=None, privileges=None):
    allow_or_deny('deny', roles, resources, privileges)


def has_user_role(role, user_id=None, request=None):
    from core.models import Roles
    if request:
        user_id = request.user.id
    if not user_id:
        raise Exception('has_user_role: bad argument')
    roles = Roles.get_by_user(user_id=user_id)
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
allow(resources=[
    'SampleViewSet',
], privileges=[GET])

allow([ROLE_ROOT], resources=['SampleViewSet'], privileges=[POST, PUT, PATCH, DELETE])

allow([ROLE_ROOT, ], 'SampleViewSet')
