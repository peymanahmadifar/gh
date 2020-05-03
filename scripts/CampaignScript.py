import os, sys
from time import sleep
import logging
import requests
from django.utils import timezone

import socket

directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, directory)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gh.settings.local")

import django

django.setup()

from django.db.models import Q
from core.models import Campaign
from core.util import broadcast
from django.conf import settings
from django import db
from django.db.utils import InterfaceError

app_name = 'CampaignScript'
logger = logging.getLogger(app_name)

# set default timeout to prevent bad delay on starting CampaignScript up!
socket.setdefaulttimeout(10)

# start your app code using sandogh project applications
logger.info('CampaignScript STARTED')

sms_on = True
email_on = True
while True:
    try:
        logger.debug('filtering campaigns to send')
    except:
        pass

    try:
        campaigns = Campaign.objects.filter(Q(status=Campaign.STATUS_NEW) | Q(status=Campaign.STATUS_RETRY))
        for campaign in campaigns:
            logger.debug('starting to send campaign %d with body %s' % (campaign.id, campaign.body))
            campaign.status = Campaign.STATUS_INPROGRESS
            campaign.start_at = timezone.now()
            campaign.save()

            if campaign.ctype == Campaign.TYPE_SMS:
                if sms_on:
                    r = broadcast.send_sms(campaign.target, campaign.body, gateway=campaign.gtw)
                    if r['status']:
                        campaign.status = Campaign.STATUS_DONE
                    else:
                        campaign.status = Campaign.STATUS_FAILED
                        logger.error('campaign %d failed!' % (campaign.id,))
                    campaign.data = r
                else:
                    campaign.status = Campaign.STATUS_DONE
            elif campaign.ctype == Campaign.TYPE_EMAIL:
                if email_on:
                    # @todo remove title from here! it should be added to the context!
                    r = broadcast.send_email(campaign.title, campaign.target, campaign.body)
                    if 'error' not in r:
                        # you must send an email
                        campaign.status = Campaign.STATUS_DONE
                    else:
                        campaign.status = Campaign.STATUS_FAILED
                        logger.error('campaign %d failed!' % (campaign.id,))
                    campaign.data = r
                else:
                    campaign.status = Campaign.STATUS_DONE
        else:
            logger.debug("No campaign found!")
    except InterfaceError:
        db.connection.close()
        logger.error('sandogh db connection error: %s' % str(e))
    except BaseException as e:
        try:
            logger.error('CampaignScript raised an error: %s' % str(e))
        except:
            pass
    sleep(5)

logger.info('CampaignScript ENDED')
