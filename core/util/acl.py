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
ROLE_ADMIN_ACC = 'admin-acc'
ROLE_ADMIN_SALES = 'admin-sales'
ROLE_CRM = 'crm'
ROLE_COUNTER = 'counter'
ROLE_ADMIN_LOG = 'admin-log'
ROLE_DRIVER = 'driver'
ROLE_ADMIN_CC = 'admin-cc'
ROLE_AGENT = 'agent'
ROLE_CONTROL = 'control'

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

# list and get branches
add_resource('BranchViewSet')

# list and get staff list of useres
add_resource('StaffViewSet')

# list, get, edit staff for admin
add_resource('StaffCoreViewSet')
add_resource('StaffsByRoleView')

# list descriptions used in kiosk
add_resource('DescriptionViewSet')
add_resource('DescriptionCategoryViewSet')
add_resource('ProductViewSet')
add_resource('ColorViewSet')
add_resource('PatternViewSet')
add_resource('GarmentViewSet')
add_resource('ProductCategoriesViewSet')
add_resource('ServiceViewSet')
add_resource('ProductServiceCostViewSet')

# list, add, delete and update customers
add_resource('CustomerViewSet')
add_resource('CustomerTypeViewSet')

# get, update and add customers with returning form in get method
add_resource('CustomerAdd')
add_resource('StaffAddressViewSet')

# list, add, delete and update bill requests
add_resource('BillViewSet')
add_resource('BillWithoutDetailsViewSet')
add_resource('ReportOnInvoicesViewSet')
add_resource('AccountViewSet')
add_resource('InvoiceDetailViewSet')

# patch request, used by driver and counter and controler
add_resource('DoneTrackRequestViewSet')
add_resource('ExitToDeliveryViewSet')
add_resource('ExitGarmentViewSet')
add_resource('ExitAllServiceRequestsViewSet')
add_resource('DeliverGarmentsViewSet')
add_resource('DeliverGarmentViewSet')


# used for customers
# add_resource('OrderDetailsView')
# add_resource('OrderScheduleDeliveryView')

# ****************************************************************************
# ACCOUNTING RESOURCES
add_resource('InvoiceViewSet')
add_resource('InvoiceV2ViewSet')
add_resource('MassiveInvoiceDetailViewSet')
add_resource('RecalculateInvoiceTotalViewSet')
add_resource('ConfirmInvoiceViewSet')
add_resource('DoneInvoiceDetailViewSet')
add_resource('UnknownInvoiceDetailViewSet')
add_resource('ReturnedInvoiceDetailViewSet')
add_resource('PatchInvoiceDetailViewSet')
add_resource('CancelInvoiceDetailViewSet')
add_resource('CancelInvoiceViewSet')
add_resource('ConfirmInvoiceViewSet')
# add_resource('TurnOversViewSet')
add_resource('TransactionsForStaffViewSet')
add_resource('UpdatePaidTransactionByInvoiceViewSet')
add_resource('TerminalViewSet')


# *****************************************************************************
# CORE APP ACLS
add_resource('UserAccountView')
add_resource('DownloadViewSet')

add_resource('ChargeAccountViewSet')
add_resource('WithdrawFromAccountViewSet')
add_resource('PayInvoiceViewSet')

# global views
# RegistrationView
# ConfirmMobileView
# RequestCodeView

# just for root role, to define all roles and all rollers
add_resource('UpdateRolesView')

add_resource('ManageConstantsView')

# *******************************************************************************
# LOGISTIC APP ACLS
add_resource('BamActionViewSet')
add_resource('MapActionViewSet')
add_resource('DriverViewSet')

# *******************************************************************************
# CALLCENTER APP ACLS

# used by FreeSWITCH to get extensions on the fly! this must be accessible by all staffs
add_resource('FSViewSet')

# used by tftp server to generate config file for Yealink ip phones.
# this must be accessible by all staffs
add_resource('ProvisionerTFTPViewSet')

# callcenter
## used to list and add campaigns
add_resource('CampaignViewSet')
## list cdrs
add_resource('CdrViewSet')

# used for list histories
add_resource('RequestHistoryViewSet')

# used for list, add, update and delete notes on request
add_resource('RequestNoteViewSet')

# shuri api
add_resource('ShuriViewSet')

# allow()
add_role(NO_ROLE)
add_role(ROLE_ROOT)

# accounting
add_role(ROLE_ADMIN_ACC)

# sales
add_role(ROLE_ADMIN_SALES)
add_role(ROLE_CRM)
add_role(ROLE_COUNTER)
add_role(ROLE_CONTROL)

# logistic
add_role(ROLE_ADMIN_LOG)
add_role(ROLE_DRIVER)

# call center
add_role(ROLE_ADMIN_CC)
add_role(ROLE_AGENT)

# *********************************************************************************
# allow root to access all of resources
allow('root')

# ********************************************************************************
# sales resources
# allow every staff to access some resources
allow(resources=[
    'BranchViewSet', 'StaffViewSet',
    'DescriptionViewSet', 'DescriptionCategoryViewSet', 'ProductViewSet',
    'ColorViewSet', 'PatternViewSet',
    'ProductCategoriesViewSet',
    'CustomerViewSet',
    'ServiceViewSet',
    'ProductServiceCostViewSet',
], privileges=[GET])

allow([ROLE_COUNTER], resources=['DescriptionViewSet', 'DescriptionCategoryViewSet'], privileges=[POST, PUT, PATCH, DELETE])

allow([ROLE_COUNTER, ROLE_DRIVER], 'GarmentViewSet')

# CustomerViewSet
allow([ROLE_AGENT, ROLE_CRM, ROLE_COUNTER], 'CustomerViewSet', privileges=[GET, POST, PUT, PATCH])

allow([ROLE_AGENT, ROLE_CRM, ROLE_COUNTER], 'CustomerTypeViewSet', privileges=[GET])

allow([ROLE_ROOT], 'CustomerViewSet', privileges=[DOWNLOAD])

# InvoiceDetailViewSet
allow([ROLE_COUNTER, ROLE_DRIVER], 'InvoiceDetailViewSet')

#
# allow(['agent'], [
#     'BillViewSet', 'CustomerAdd'
# ])

# CustomerAdd
allow([ROLE_COUNTER, ROLE_CRM, ROLE_AGENT], ['CustomerAdd', 'StaffAddressViewSet'])

# BillViewSet
allow([ROLE_COUNTER, ROLE_CRM, ROLE_AGENT], [
    'BillViewSet',
    'BillWithoutDetailsViewSet',
    'InvoiceViewSet'
], [GET, PUT, PATCH])

allow([ROLE_ADMIN_ACC], [
    'BillViewSet',
    'BillWithoutDetailsViewSet',
    'InvoiceViewSet'
], [GET])

allow([ROLE_COUNTER], 'BillViewSet', [POST, PRIVILEGE_INVOICE_EDIT])
allow(ROLE_CONTROL, [
    'BillViewSet',
    'BillWithoutDetailsViewSet',
], GET)
allow(ROLE_ADMIN_ACC, 'ReportOnInvoicesViewSet', GET)

allow([ROLE_COUNTER, ROLE_DRIVER], [
    'DoneTrackRequestViewSet',
    'ExitToDeliveryViewSet',
    'ExitAllServiceRequestsViewSet',
    'DeliverGarmentsViewSet',
    'DeliverGarmentViewSet'
], [PATCH])

allow([ROLE_ADMIN_ACC, ROLE_AGENT], [
    'ExitToDeliveryViewSet',
    'ExitAllServiceRequestsViewSet',
    'DeliverGarmentsViewSet',
    'DeliverGarmentViewSet'
], [PATCH])

allow([ROLE_COUNTER], [
    'ExitGarmentViewSet'
], [PATCH])

# accounting module allowance
allow([ROLE_COUNTER, ROLE_DRIVER], [
    'InvoiceV2ViewSet'
])

allow([ROLE_ADMIN_ACC], [
    'TerminalViewSet'
], [GET])


allow([ROLE_COUNTER, ROLE_DRIVER], [
    'MassiveInvoiceDetailViewSet'
], [POST])

allow(ROLE_COUNTER, 'RecalculateInvoiceTotalViewSet', PATCH)

# logistic module allowance
allow(ROLE_CONTROL, ['BamActionViewSet', 'MapActionViewSet'], [GET, PATCH])

allow(ROLE_CRM, 'DriverViewSet')
allow([ROLE_COUNTER, ROLE_AGENT], 'DriverViewSet', [GET])

# CampaignViewSet
allow([ROLE_COUNTER, ROLE_CRM, ROLE_AGENT], 'CampaignViewSet', [GET, POST])
allow(ROLE_ADMIN_CC, 'CdrViewSet', GET)

# RequestHistoryViewSet
allow([ROLE_COUNTER, ROLE_CRM, ROLE_AGENT], 'RequestHistoryViewSet', [GET])
allow([ROLE_COUNTER, ROLE_CRM, ROLE_AGENT], 'RequestNoteViewSet')

allow(ROLE_COUNTER, 'ShuriViewSet')
# core app permissions
# allow('agent', 'UserAccountView')
allow(resources='StaffsByRoleView')

# access to accounting resources
allow([ROLE_COUNTER, ROLE_DRIVER], ['PayInvoiceViewSet'])
allow([ROLE_ADMIN_ACC, ROLE_ADMIN_SALES], ['ChargeAccountViewSet'])
allow(ROLE_ADMIN_ACC, 'WithdrawFromAccountViewSet')
allow([ROLE_ADMIN_ACC, ROLE_AGENT], 'PayInvoiceViewSet')
allow(ROLE_CONTROL, [
    'DoneInvoiceDetailViewSet',
    'UnknownInvoiceDetailViewSet',
    'ReturnedInvoiceDetailViewSet',
    'PatchInvoiceDetailViewSet'])
allow([ROLE_COUNTER, ROLE_DRIVER], [
    'CancelInvoiceDetailViewSet',
    'CancelInvoiceViewSet',
    'ConfirmInvoiceViewSet'
])

allow([ROLE_ADMIN_ACC], ['TransactionsForStaffViewSet', 'AccountViewSet', 'UpdatePaidTransactionByInvoiceViewSet'])
