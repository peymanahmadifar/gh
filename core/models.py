from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from .util import extend
from django.utils.translation import ugettext_lazy as _
# extend.TrackModel = core.util.extend.extend.TrackModel
# from .utils import extract_user_roles
from django.db.models.signals import pre_save, post_save
# from accounting.helpers import create_or_update_account
from django.dispatch import receiver


# add a signal to user model at adding new user to create account for him/her
# for now we create account for everybody! staff or customer! It may help us in the future
# @receiver(post_save, sender=User)
# def user_post_save(sender, instance, created, **kwargs):
#     if created:
#         create_or_update_account(instance)


# Create your models here.
class Confirm(extend.TrackModel):
    class Meta:
        verbose_name = "تأیید"
        verbose_name_plural = "تأییدات"
        abstract = False
        unique_together = ('user', 'which',)

    WHICH_EMAIL = 1
    WHICH_MOBILE = 2
    WHICH_RESET_PASSWORD = 10
    WHICH_CHOICES = (
        (WHICH_EMAIL, 'Email'),
        (WHICH_MOBILE, 'Mobile'),
        (WHICH_RESET_PASSWORD, 'Reset Password')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    which = models.IntegerField(choices=WHICH_CHOICES, default=WHICH_MOBILE)

    # reasonable for uuid or each other thing you want
    code = models.CharField(max_length=36)
    # how many times user try to get confirmed
    count = models.IntegerField(default=1)

    _which_choices = None

    @staticmethod
    def get_which_label(id):
        if Confirm._which_choices == None:
            Confirm._which_choices = {}
            for i in Confirm.WHICH_CHOICES:
                Confirm._which_choices[str(i[0])] = i[1]
        return Confirm._which_choices[str(id)]

    def __str__(self):
        return self.user.username + ' which id:' + Confirm.get_which_label(self.which)


class Roles(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roles = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'roles')

    # @staticmethod
    # def extract_and_update_roles(tree_node):
    #     new_roles = {}
    #     units = tree_node['children']
    #     for unit in units:
    #         roles = unit['children']
    #         for role in roles:
    #             if 'children' in role:
    #                 users = role['children']
    #                 for user in users:
    #                     user_id = user['staff_id']
    #                     if str(user_id) not in new_roles:
    #                         new_roles[str(user_id)] = []
    #                     new_roles[str(user_id)].append(role['id'])

    # @todo rollback if any error occurred!

    # remove old roles
    # Roles.objects.all().delete()

    # add new roles
    # for user_id in new_roles:
    #     Roles(user_id=user_id, roles=new_roles[user_id]).save()

    @staticmethod
    def get_by_user(user_id=None):
        roles = []
        try:
            model = Roles.objects.get(user_id=user_id)
            roles = model.roles
        except Roles.DoesNotExist:
            pass
        finally:
            # print(roles)
            if User.objects.get(id=user_id).is_superuser:
                roles.append('root')
            if not roles:
                roles.append('no_role')
        return roles

    @staticmethod
    def get_users_by_role(role):
        users = []
        for user_role in Roles.objects.all():
            if role in user_role.roles:
                users.append(user_role.user)
        return users


class Preferences(extend.TrackModel):
    PREF_KEY_CONSTANTS = 'constants'

    class Meta:
        verbose_name = "تنظیم"
        verbose_name_plural = "تنظیمات"
        abstract = False

    key = models.CharField(unique=True, max_length=100)
    value = JSONField(default=dict)

    @staticmethod
    def get(key, default=None):
        try:
            obj = Preferences.objects.get(key=key)
        except Preferences.DoesNotExist:
            return default

        return obj.value['__string__'] if '__string__' in obj.value else obj.value

    @staticmethod
    def set(key, value):
        try:
            obj = Preferences.objects.get(key=key)
        except Preferences.DoesNotExist:
            obj = Preferences()
            obj.key = key

        if type(value) == str:
            obj.value = {'__string__': value}

        obj.value = value
        obj.save()


class MobileTemp(extend.TrackModel):
    class Meta:
        verbose_name = "شماره بالقوه"
        verbose_name_plural = "شماره‌های بالقوه"
        abstract = False

    number = models.CharField(max_length=20, verbose_name=_('شماره'), unique=True)
    ip = models.GenericIPAddressField(verbose_name=_('آی‌پی'))


class PrefConstants():
    GENERAL_DISCOUNT_PERCENT = 'general_discount_percent'
    GENERAL_DISCOUNT_START_DATE = 'general_discount_start_date'
    GENERAL_DISCOUNT_END_DATE = 'general_discount_end_date'

    EVENT_BASED_MESSAGE = 'event_based_message'
    EBM_START_DATE = 'ebm_start_date'
    EBM_END_DATE = 'ebm_end_date'

    @staticmethod
    def get_holidays():
        return PrefConstants.get().get('holidays', [])

    @staticmethod
    def get_exceed_capacity():
        return PrefConstants.get().get('exceed_capacity', [])

    @staticmethod
    def get_android_new_features():
        return PrefConstants.get().get('android_new_features', '')

    @staticmethod
    def get_ios_new_features():
        return PrefConstants.get().get('ios_new_features', '')

    @staticmethod
    def get_general_discount_percent() -> int:
        """
        :rtype: int
        """
        return PrefConstants.get().get(PrefConstants.GENERAL_DISCOUNT_PERCENT, 0)

    @staticmethod
    def get_general_discount_start_date():
        return PrefConstants.get().get(PrefConstants.GENERAL_DISCOUNT_START_DATE, '0000-00-00')

    @staticmethod
    def get_general_discount_end_date():
        return PrefConstants.get().get(PrefConstants.GENERAL_DISCOUNT_END_DATE, '0000-00-00')

    @staticmethod
    def get_by_key(key, default=None):
        return PrefConstants.get().get(key, default)

    @staticmethod
    def get():
        return Preferences.get('constants', {})

    @staticmethod
    def set(value):
        Preferences.set('constants', value)


class Download(models.Model):
    class Meta:
        verbose_name = "دانلود"
        verbose_name_plural = "دانلودها"
        abstract = False

    path = models.CharField(max_length=256, db_index=True)
    ip = models.GenericIPAddressField(verbose_name=_('آی‌پی'), default='', blank=True, null=True)
    at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
