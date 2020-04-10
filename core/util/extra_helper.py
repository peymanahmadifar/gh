import hashlib
from . import lang
from django.db.models import Q
import logging
import re
from django.core.exceptions import FieldDoesNotExist

logger = logging.getLogger('script')

def md5sum(string):
    m = hashlib.md5()
    m.update(string)
    return m.hexdigest()

def play_download(view, cb=None, header=None, rows=None, footer=None):
    import xlsxwriter, tempfile
    from io import BytesIO
    from django.http import HttpResponse
    from wsgiref.util import FileWrapper
    output = BytesIO()

    # tf = tempfile.TemporaryFile()
    workbook = xlsxwriter.Workbook(output, {
        'excel2003_style': True,
        'in_memory': True
    })
    worksheet = workbook.add_worksheet()
    cell_format_bold = workbook.add_format({'bold': True, 'font_color': 'black'})
    '''
    just super user can call this method

    @see http://xlsxwriter.readthedocs.io/getting_started.html#installing-xlsxwriter
    @see http://xlsxwriter.readthedocs.io/tutorial01.html#tutorial1
    '''
    queryset = view.filter_queryset(view.get_queryset())

    if header:
        col = 0
        for key in header:
            worksheet.write(0, col, key, cell_format_bold)
            col += 1
    if rows:
        row = 1
        for data in rows:
            col = 0
            for value in data:
                if type(value) != int:
                    worksheet.write(row, col, str(value))
                else:
                    worksheet.write_number(row, col, value)
                col += 1
            row += 1
    elif cb:
        row = 1
        for item in queryset:
            data = cb(item, row)
            if not data:
                continue
            col = 0
            for value in data:
                if type(value) != int:
                    worksheet.write(row, col, str(value))
                else:
                    worksheet.write_number(row, col, value)
                col += 1
            row += 1
    else:
        serializer = view.get_serializer(queryset, many=True)
        serializer_class = view.get_serializer_class()
        model = serializer_class.Meta.model
        if serializer.data:
            choices = {}
            keys = serializer.data[0].keys()
            col = 0
            for key in keys:
                worksheet.write(0, col, key)
                try:
                    field = model._meta.get_field(key)
                    if hasattr(field, 'choices') and field.choices:
                        buff = {}
                        for choice_value, choice_label in field.choices:
                            buff[str(choice_value)] = str(choice_label)
                        choices[str(key)] = buff
                except FieldDoesNotExist as e:
                    pass
                col += 1

            row = 1
            for data in serializer.data:
                col = 0
                for key, value in data.items():
                    new_value = str(value) if str(key) not in choices or str(value) not in choices[str(key)] else choices[str(key)][str(value)]
                    # buff = '%s__%s__%s' % (str(value), str(key), new_value)
                    worksheet.write(row, col, new_value)
                    col += 1
                row += 1
    if footer:
        data = footer()
        col = 0
        for value in data:
            new_value = str(value)
            worksheet.write(row, col, new_value, cell_format_bold)
            col += 1
        row += 1
    workbook.close()
    response = HttpResponse(output.getvalue(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=request.xlsx'
    return response

def play_filtering_form(queryset, query_params):
    kwargs_and = {}
    kwargs_exclude = {}
    for param in query_params:
        value = query_params.get(param)

        if not value:
            continue
        if value == 'None':
            value = None
        _param = re.sub('\[\d+\]', '', param)

        if param[:7] == 'filter_':

            if value in ('0', '1'):
                value = int(value)
            # print(param, value, "\n")
            pattern = ''
            if ('pattern_' + param) in query_params:
                pattern = query_params.get('pattern_' + param)
            key = _param[7:] + pattern
            try:
                value = lang.fix_chars(value)
            except:
                pass
            kwargs_and[key] = value
        elif param[:9] == 'orfilter_':
            pattern = ''
            if ('pattern_' + param) in query_params:
                pattern = query_params.get('pattern_' + param)
            key_string = param[9:]
            keys = key_string.split('OR')
            value_split = value.split('OR')
            QBuff = None
            counter = -1
            for key in keys:
                counter += 1
                if len(value_split) > 1:
                    value = value_split[counter]
                    if not value:
                        continue
                if not QBuff:
                    QBuff = Q(**{str(key + pattern): value})
                else:
                    QBuff |= Q(**{str(key + pattern):value})
            if QBuff:
                queryset = queryset.filter(QBuff)
        elif param[:8] == 'order_by':
            # queryset = queryset.order_by()
            args = value.split(',')
            queryset = queryset.order_by(*args)        
        elif param[:8] == 'distinct':
            # queryset = queryset.order_by()
            args = value.split(',')
            queryset = queryset.distinct(*args)
        elif param[:8] == 'exclude_':
            if value in ('0', '1'):
                value = int(value)
            pattern = ''
            if ('pattern_' + param) in query_params:
                pattern = query_params.get('pattern_' + param)
            key = _param[8:] + pattern
            try:
                value = lang.fix_chars(value)
            except:
                pass
            kwargs_exclude[key] = value
    logger.debug('kwargs_and to filter: %s. kwargs_exclude to filter: %s%s' % (kwargs_and, kwargs_exclude, "\n"))
    if kwargs_and:
        queryset = queryset.filter(**kwargs_and)
    if kwargs_exclude:
        queryset = queryset.exclude(**kwargs_exclude)
    return queryset


def get_ip(request):
    """Returns the IP of the request, accounting for the possibility of being
    behind a proxy.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(", ")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip
