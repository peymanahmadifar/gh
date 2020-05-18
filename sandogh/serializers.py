import random
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from core.util.extend import CellphoneField, get_from_header
from core.models import UserMeta, Campaign
from . import models
from .models import Member


class LenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lender
        fields = '__all__'


class InviteMemberSerializer(serializers.Serializer):
    mobile = CellphoneField(label=_('Cellphone'), required=True)

    def create(self, validated_data):
        request = self.context.get('request')
        sandogh_id = get_from_header('Sandogh-Id', request)
        mobile = validated_data.get('mobile')
        username = str(mobile)
        password = str(random.randrange(100000, 999999))
        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()
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
            raise serializers.ValidationError(
                {"mobile": _("The mobile number has already been registered in the system.")})
        return attrs


class VerifyUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    status = serializers.ChoiceField(choices=(
        (UserMeta.STATUS_REJECT, 'rejected'),
        (UserMeta.STATUS_VERIFY, 'verified')
    ))

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        status = validated_data.get('status')
        user = User.objects.get(pk=user_id)
        user.usermeta.status = status
        user.usermeta.save()
        # @Todo send verify/reject messege/notification to the user
        return validated_data

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        request = self.context.get('request')
        lender_id = get_from_header('Sandogh-Id', request)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": _("User not found.")})
        if not Member.objects.filter(lender_id=lender_id).exists():
            raise serializers.ValidationError({"user_id": _("The user is not a member of the lender.")})
        if user.usermeta.status == UserMeta.STATUS_VERIFY:
            raise serializers.ValidationError({"user_id": _("The user is verified and the status cannot be changed.")})
        return attrs
