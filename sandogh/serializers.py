import random
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from core.util.extend import CellphoneField, get_from_header
from core.models import UserMeta, Campaign
from . import models


class LenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lender
        fields = '__all__'


class MobileSerializer(serializers.Serializer):
    mobile = CellphoneField(label=_('Cellphone'), required=True)

    def create(self, validated_data):
        request = self.context.get('request')
        sandogh_id = get_from_header('Sandogh-Id', request)
        username = 'user' + str(random.randrange(100000, 999999))
        password = str(random.randrange(100000, 999999))
        mobile = validated_data.get('mobile')
        user = User.objects.create(username=username, password=password)
        UserMeta.objects.create(user=user, mobile=mobile)
        models.Member.objects.create(user=user, lender_id=sandogh_id)
        Campaign.send_sms(gtw=Campaign.GTW_PARSA_TEMPLATE_SMS,
                          to=mobile,
                          target_user=user,
                          tpl='inviteMember',
                          context=dict(
                              param1=username,
                              param2=password
                          ))
        return validated_data

    def validate(self, attrs):
        request = self.context.get('request')
        try:
            staff_id = get_from_header('Staff-Id', request)
            sandogh_id = get_from_header('Sandogh-Id', request)
        except Exception as e:
            raise serializers.ValidationError(e)
        if sandogh_id != models.Staff.objects.get(pk=staff_id).lender_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(_("You dont have permission to invite a member to this lender."))
        from core.models import UserMeta
        mobile = attrs.get('mobile')
        um = UserMeta.objects.filter(mobile=mobile)
        if um:
            raise serializers.ValidationError(_("The mobile number has already been registered in the system."))
        return attrs
