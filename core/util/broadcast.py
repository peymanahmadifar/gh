import logging
import requests
import json
# import mandrill
from zeep import Client
from django.template.loader import render_to_string
from django.core.mail import send_mail
from core.models import Campaign
from django.conf import settings

parsa_client = None


def get_parsa_client():
    global parsa_client
    if not parsa_client:
        try:
            parsa_client = Client("http://parsasms.com/webservice/v2.asmx?WSDL")
        except:
            pass
    return parsa_client


# app_name = 'pakand'
logger = logging.getLogger()

sms = {
    "from": "30007227001821",
    "username": "emami",
    "password": "emami",
    "url": "http://tsms.ir/url/tsmshttp.php?from=%(from)s&"
           "to=%(to)s&username=%(username)s&"
           "password=%(password)s&message=%(message)s"
}

ERROR_REASONS_PARSA = {
    '1': 'نام کاربری یا رمز عبور معتبر نمی‌باشد.',
    '2': 'آرایه‌ها خالی می‌باشد.',
    '3': 'طول آرایه بیشتر از ۱۰۰ می‌باشد.',
    '4': 'طول آرایه‌ی فرستنده و گیرنده و متن پیام با یکدیگر تطابق ندارد.',
    '5': 'امکان گرفتن پیام جدید وجود ندارد.',
    '6': 'حساب کاربری غیر فعال می‌باشد. '
         + 'نام کاربری و یا رمز عبور خو را به درستی وارد نمی‌کنید.'
         + 'در صورتی که به تازگی وب سرویس را فعال کرده‌اید از منوی تنظیمات رمز عبور رمز عبور وب سرویس خود را مجدد ست کنید.',
    '7': 'امکان دسترسی به خط مورد نظر وجود ندارد.',
    '8': 'شماره گیرنده نامعتبر است.',
    '9': 'حساب اعتبار ریالی مورد نیاز را دارا نمی‌باشد.',
    '10': 'خطایی در سیستم رخ داده است. دوباره سعی کنید.',
    '11': 'ip نامعتبر است',
    '20': 'شماره مخاطب فیلتر شده می‌باشد.',
    '21': 'ارتباط با سرویس‌دهنده قطع می‌باشد.',
}


def send_sms(to, message, gateway=Campaign.GTW_PARSA_SMS, logger=logger):
    result = dict(
        status=False,
        body=None
    )

    try:
        if gateway == Campaign.GTW_PARSA_SMS:
            body = None
            if 'message' in message:
                body = message['message']
            elif 'tpl' in message:
                try:
                    body = render_to_string(message['tpl'], message['context'])
                except:
                    pass
            if not body:
                raise Exception('body is null for GTW_PARSA_SMS!')
            if get_parsa_client():
                r = get_parsa_client().service.SendSMS(
                    '****',
                    '*****',
                    {'string': ['30006708537537']},
                    {'string': [to]},
                    {'string': [body]}
                )

                result['status'] = r and hasattr(r, 'long') and r.long[0] > 1000
                result['body'] = r.long if r and hasattr(r, 'long') else None
                if not result['status']:
                    error_code = str(result.get('body')[0]) if result.get('body', []) else '-1'
                    result['error'] = ERROR_REASONS_PARSA.get(error_code, '')

            else:
                result['status'] = False
                result['body'] = None
                result['error'] = 'parsa sms connection failed!'
        if gateway == Campaign.GTW_PARSA_TEMPLATE_SMS:
            if 'tpl' in message:
                tpl = message['tpl']
                payload = {'receptor': to, 'template': tpl}
                payload.update(message.get('context', {}))
                if 'type' not in payload:
                    payload['type'] = 1
                headers = {'apikey': settings.PARSA_TEMPLATE_SMS_APIKEY,
                           'content-type': "application/x-www-form-urlencoded"
                           }
                r = requests.post("http://api.smsapp.ir/v2/send/verify", data=payload, headers=headers)

                resp = json.loads(r.text)
                result['body'] = resp
                if 'result' not in resp:
                    raise Exception('result is not in parsa sms response!')
                result['status'] = resp['result'] == 'success'
            else:
                raise Exception('tpl does not exist!')
        else:
            raise Exception('gateway is wrong')
            sms_data = sms.copy()
            url_template = sms_data['url']
            del sms_data['url']
            sms_data['message'] = message
            sms_data['to'] = to
            url = url_template % sms_data

            # call api
            logger.debug('calling url %s' % url)
            r = requests.get(url)
            result['status'] = (r.status_code == 200)
            # @todo result body should be returned and saved
            result['body'] = None
    except BaseException as e:
        result['status'] = False
        result['error'] = str(e)

    return result


def send_email(subject, to, message, sender='خشکشویی پاکان <salam@pakan.ir>', from_name='Pakan Dry Cleaning',
               logger=logger, gtw=Campaign.GTW_DJANGO_SEND_MAIL):
    # https://mandrillapp.com/api/docs/messages.python.html#method-send-raw
    try:
        html = ''
        if 'message' in message:
            html = message['message']
        elif 'tpl' in message:
            try:
                html = render_to_string(message['tpl'], message['context'])
            except:
                pass
        else:
            html = message

        if gtw == Campaign.GTW_DJANGO_SEND_MAIL:
            if type(to) != list:
                to_list = [to]

            res = send_mail(
                subject,
                html,
                sender,
                to_list,
                html_message=html,
                fail_silently=False,
            )

            result = {
                'status': 'sent',
            }
            if res == 0:
                result['status'] = 'not-sent'
                result['error'] = 1
        else:
            raise Exception('mandrill is not supported for now!')
            mandrill_client = mandrill.Mandrill('0zCcaHCR9Ogrz-ryQ6kU8A')
            if type(to) != list:
                to_list = [{'email': to}]
            # uncomment to send by mandrill
            message = {
                'html': html,
                'subject': subject,
                'from_email': sender,
                'from_name': from_name,
                'to': to_list,
            }
            return mandrill_client.messages.send(
                message=message,
                async=False,
                ip_pool='Main Pool')
        return result

        '''
        [{'_id': 'abc123abc123abc123abc123',
          'email': 'recipient.email@example.com',
          'reject_reason': 'hard-bounce',
          'status': 'sent'}]
        '''

    # except mandrill.Error as e:
    #     return {"error": 'A mandrill error occurred: %s - %s' % (e.__class__, e)}

    except BaseException as e:
        return {"error": str(e)}
