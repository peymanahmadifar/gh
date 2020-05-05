import logging

logger = logging.getLogger('django')

ROLE_TEST = None
# ROLE_TEST = 'crm'
# ROLE_TEST = 'kiosk'

# private variables
resources = []
roles = []
permissions = {}

# request methods
GET = 'get'
PUT = 'put'
PATCH = 'patch'
POST = 'post'
DELETE = 'delete'
DOWNLOAD = 'download'


# all privileges come here!
# PRIVILEGE_INVOICE_EDIT = 'invoice-edit'


def is_allowed(resource, privilege=None, roles=None):
    # return false if the resource id does not exist.
    if not _has_resource(resource):
        raise Exception('resource %s does not exist! add it to core/util/acl.py' % resource)

    if ROLE_TEST:
        roles = [ROLE_TEST]

    if not roles:
        raise Exception('is_allowed: roles must be set')

    if resource in permissions:
        for role in roles:
            if not _has_role(role):
                raise Exception('role %s does not exist!' % role)
            if role in permissions[resource]:
                if not privilege or not permissions[resource][role]['privileges'] or privilege in \
                        permissions[resource][role]['privileges']:
                    return True
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


def add_role(roles_array):
    global roles
    for role in roles_array:
        if not role in roles:
            roles.append(role)


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
