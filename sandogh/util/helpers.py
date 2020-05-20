from sandogh.models import Staff


def get_from_header(key, request, raise_exception=True):
    if not request.headers.get(key):
        if raise_exception:
            raise Exception('The %s must be set in the request header' % key)
        else:
            return None
    else:
        return int(request.headers.get(key))


def get_staff(request):
    staff_id = get_from_header('staff-id', request)
    try:
        staff = Staff.objects.get(pk=staff_id)
    except Staff.DoesNotExist:
        raise Exception('Staff not found')
    return staff
