from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from core.serializers import UserSerializer
from core.util.extend import CellphoneField
from core.models import UserMeta, Campaign

from .models import Member, Lender, Staff, Role
from .util.helpers import get_staff
from .util.permissions import roles, staff_has_role


class LenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lender
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    lender = LenderSerializer()

    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ('user', 'lender')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role']


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    lender = LenderSerializer()
    role_set = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = Staff
        fields = '__all__'
        read_only_fields = ('user', 'lender')


class InviteMemberSerializer(serializers.Serializer):
    mobile = CellphoneField(label=_('Cellphone'), required=True)

    def create(self, validated_data):
        request = self.context.get('request')
        staff = get_staff(request)
        mobile = validated_data.get('mobile')
        username = str(mobile)
        password = str(mobile)[-4:]
        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()
        UserMeta.objects.create(user=user, mobile=mobile)
        Member.objects.create(user=user, lender=staff.lender)
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
        tpl = 'verfyUserTemplate' if status == UserMeta.STATUS_VERIFY else 'rejectUserTemplate'
        Campaign.send_sms(gtw=Campaign.GTW_PARSA_TEMPLATE_SMS,
                          to=user.usermeta.mobile,
                          target_user=user,
                          tpl=tpl,
                          # @Todo set params according to template when the template defined
                          context=dict(
                              param1=status,
                          ))
        return validated_data

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        request = self.context.get('request')
        staff = get_staff(request)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": _("User not found.")})
        if not Member.objects.filter(lender=staff.lender).exists():
            raise serializers.ValidationError({"user_id": _("The user is not a member of the lender.")})
        if user.usermeta.status == UserMeta.STATUS_VERIFY:
            raise serializers.ValidationError({"user_id": _("The user is verified and the status cannot be changed.")})
        return attrs


class AssignRoleSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField(required=True)
    role = serializers.CharField(required=True, max_length=60)

    def create(self, validated_data):
        staff_id = validated_data.get('staff_id')
        role = validated_data.get('role')
        Role.objects.create(staff_id=staff_id, role=role)
        return validated_data

    def validate(self, attrs):
        staff_id = attrs.get('staff_id')
        role = attrs.get('role')
        if not role in roles:
            raise serializers.ValidationError({"role": _("Role does not exists.")})
        request = self.context.get('request')
        request_staff = get_staff(request)
        try:
            staff = Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            raise serializers.ValidationError({"staff_id": _("Staff not found.")})
        if staff.lender != request_staff.lender:
            raise serializers.ValidationError({"staff_id": _("The staff do not belong to the lender.")})
        if staff_has_role(role=role, staff_id=staff_id):
            raise serializers.ValidationError({"role": _("Duplicated role.")})
        return attrs
