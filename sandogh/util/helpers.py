from core.util.extend import get_from_header
from sandogh.models import Staff


def get_staff(request):
    staff_id = get_from_header('staff-id', request)
    try:
        staff = Staff.objects.get(pk=staff_id)
    except Staff.DoesNotExist:
        raise Exception('Staff not found')
    return staff
