from django.db import models

from core.util import extend
import datetime, uuid
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField


def upload_to_documents(instance, filename):
    pattern = 'photo/%d_%s.%s'
    _ext = filename.split('.')[-1]
    return pattern % (instance.id, uuid.uuid1(), _ext)


# Create your models here.
class Borrower(extend.TrackModel):
    class Meta:
        verbose_name = "وام گيرنده"
        verbose_name_plural = "وام گیرندگان"

    GENDER_UNKNOWN = -1
    GENDER_FEMALE = 0
    GENDER_MALE = 1
    GENDER = (
        (GENDER_UNKNOWN, _('Unknown')),
        (GENDER_MALE, _('Male')),
        (GENDER_FEMALE, _('Female')),
    )

    REGISTRATION_GTW_UNKNOWN = 0
    REGISTRATION_GTW_WEB = 1
    REGISTRATION_GTW_TELEGRAM = 20
    REGISTRATION_GTW_ANDROID = 30
    REGISTRATION_GTW_IPHONE = 31
    REGISTRATION_GTW_CHOICES = (
        (REGISTRATION_GTW_UNKNOWN, 'Unknown'),
        (REGISTRATION_GTW_WEB, 'Web'),
        (REGISTRATION_GTW_TELEGRAM, 'Telegram'),
        (REGISTRATION_GTW_ANDROID, 'Android'),
        (REGISTRATION_GTW_IPHONE, 'Iphone'),
    )

    NOT_CONFIRMED = False
    CONFIRMED = True
    MOBILE_CONFIRM_CHOICES = (
        (NOT_CONFIRMED, _('Not confirmed')),
        (CONFIRMED, _('Confirmed'))
    )

    mobile = models.CharField(max_length=100, verbose_name=_('Mobile'), blank=True, null=True, default='',
                              db_index=True)
    tel = models.CharField(max_length=30, default='', blank=True, verbose_name=_('Telephone 1'), db_index=True)
    tel2 = models.CharField(max_length=30, default='', blank=True, verbose_name=_('Telephone 2'), db_index=True)
    fax = models.CharField(max_length=100, default='', blank=True, verbose_name=_('Fax'), db_index=True)

    desc = models.CharField(max_length=1024, default='', blank=True, verbose_name=_('Description'))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('Birth Date'))
    birthday = models.CharField(max_length=4, default='0000', blank=True, verbose_name=_('Birth Day'),
                                editable=False)

    # 1 = man 0 = woman
    sex = models.SmallIntegerField(choices=GENDER, blank=True, null=True, default=GENDER_UNKNOWN,
                                   verbose_name=_('Gender'))

    membership = models.DateField(default=datetime.date.today, verbose_name=_('Membership'), blank=True, null=True)
    # branch = models.ForeignKey(Branch, blank=True, null=True, verbose_name=_('Branch'), on_delete=models.SET_NULL)
    # is_company = models.BooleanField(default=False, verbose_name=_('Is Company?'))

    # is_department = models.BooleanField(default=False, verbose_name=_('Is Department?'))
    notification = models.CharField(max_length=1024, default='', blank=True, verbose_name=_('Notification'))

    # login
    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_('User Identification'),
                                on_delete=models.CASCADE)
    mobile_confirm = models.BooleanField(choices=MOBILE_CONFIRM_CHOICES, default=False,
                                         verbose_name=_('Mobile Confirm'))
    email_confirm = models.BooleanField(choices=MOBILE_CONFIRM_CHOICES, default=False,
                                        verbose_name=_('Email Confirm'))

    def __str__(self):
        return "%s %s" % ("مشتری", self.get_name())

    def get_name(self):
        if not self.user:
            return 'has-no-user!'
        return '%s-%s' % (self.user.last_name, self.user.first_name)


class Lender(extend.TrackModel):
    class Meta:
        verbose_name = "صندوق"
        verbose_name_plural = "صندوق‌ها"

    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=60, default='')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_('admin username'),
                              on_delete=models.CASCADE)


class Staff(extend.TrackModel):
    class Meta:
        verbose_name = "کارمند"
        verbose_name_plural = "کارمندها"

    lender = models.ForeignKey('Lender', on_delete=models.PROTECT)

    # perhaps login is not good naming for now,
    # it means a relation to User model...
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})

    def __str__(self):
        return (self.user.username if self.user else 'nouser') + ', ' + self.lender.name


class Role(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=60)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('staff', 'role')

    def __str__(self):
        return self.role

    @staticmethod
    def get_by_staff(staff_id=None):
        roles = []
        try:
            for role in Role.objects.filter(staff_id=staff_id):
                roles.append(role.role)
        finally:
            if not roles:
                roles.append('no_role')
        return roles

    @staticmethod
    def get_staff_by_role(role):
        staffs = []
        for staff_role in Role.objects.filter(role=role):
            staffs.append(staff_role.staff)
        return staffs


class Member(extend.TrackModel):
    class Meta:
        verbose_name = "عضو"
        verbose_name_plural = "اعضا"

    lender = models.ForeignKey('Lender', on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    debt = models.BigIntegerField(default=0)


class Request(extend.TrackModel):
    class Meta:
        verbose_name = "درخواست"
        verbose_name_plural = "درخواست‌ها"

    TYPE1 = 1
    TYPE2 = 2
    TYPE_CHOICES = (
        (TYPE1, 'TYPE1'),
        (TYPE2, 'TYPE2'),
    )

    STATUS_NEW = 1
    STATUS_CONFIRMED = 2
    STATUS_REJECTED = 10
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_REJECTED, 'Rejected'),
    )

    requester = models.ForeignKey('Member', on_delete=models.CASCADE)
    type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE1)
    body = models.CharField(max_length=100, default='')
    date = models.DateField(auto_now_add=True)
    staff_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, max_length=300, default='', on_delete=models.CASCADE)
    staff_review_body = models.CharField(max_length=300, default='')
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)


class Document(extend.TrackModel):
    class Meta:
        verbose_name = "مدرک"
        verbose_name_plural = "مدارک"

    TYPE_NATIONAL_CARD = 1
    TYPE_BIRTH_CERTIFICATE = 2
    TYPE_PORTRAIT = 3
    TYPE_SIGN = 4
    TYPE_STAMP = 5
    TYPE_CHOICES = (
        (TYPE_NATIONAL_CARD, 'کارت ملی'),
        (TYPE_BIRTH_CERTIFICATE, 'شناسنامه'),
        (TYPE_PORTRAIT, 'عکس'),
        (TYPE_SIGN, 'امضا'),
        (TYPE_STAMP, 'مهر'),
    )
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_to_documents)


# nobat
class Turn(extend.TrackModel):
    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"

    request = models.ForeignKey('Request', on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    due_date = models.DateField()


class StaffReport(extend.TrackModel):
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enter_at = models.DateTimeField()
    exit_at = models.DateTimeField()
    desc = models.CharField(max_length=512, default='', blank=True)
    performance = models.IntegerField(default=0, blank=True)


class Payment(extend.TrackModel):
    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    TYPE_INSTALLMENT = 0
    TYPE_SAVING = 1
    TYPE_CHOICES = (
        (TYPE_INSTALLMENT, 'قسط'),
        (TYPE_SAVING, 'پس انداز')
    )
    amount = models.BigIntegerField()
    datetime = models.DateTimeField()
    type = models.IntegerField(choices=TYPE_CHOICES)
    terminal = models.ForeignKey('Terminal', on_delete=models.PROTECT)
    desc = models.CharField(max_length=512, default='', blank=True)
    serial = models.CharField(max_length=20, default='', blank=True)


class Announcement(extend.TrackModel):
    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلانات"

    TYPE_NOTIFICATION = 1
    TYPE_RULE = 2
    TYPE_CHOICES = (
        (TYPE_NOTIFICATION, 'اطلاعیه'),
        (TYPE_RULE, 'مقررات')
    )
    body = models.TextField(default='')
    type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE_NOTIFICATION)
    lender = models.ForeignKey('Lender', on_delete=models.PROTECT)
    publish_at = models.DateTimeField()


class Bank(extend.TrackModel):
    CODES_SHAHR = 19
    CODES_CHOICES = (
        (1, "آینده"),
        (2, "اقتصاد نوین"),
        (3, "ایران زمین"),
        (4, "انصار"),
        (5, "پست بانک"),
        (6, "پاسارگاد"),
        (7, "پارسیان"),
        (8, "تجارت"),
        (9, "توسعه صادرات"),
        (10, "توسعه تعاون"),
        (11, "حکمت"),
        (12, "خاورمیانه"),
        (13, "دی"),
        (14, "رفاه"),
        (15, "سامان"),
        (16, "سرمایه"),
        (17, "سینا"),
        (18, "سپه"),
        (19, "شهر"),
        (20, "قرض الحسنه رسالت"),
        (21, "قرض الحسنه مهر"),
        (22, "قوامین"),
        (23, "کشاورزی"),
        (24, "کارآفرین"),
        (25, "صنعت و معدن"),
        (26, "صادرات"),
        (27, "گردشگری"),
        (28, "ملت"),
        (29, "مسکن"),
        (30, "ملی")
    )

    class Meta:
        verbose_name = "بانک"
        verbose_name_plural = "بانک‌ها"

    name = models.CharField(max_length=100)
    code = models.IntegerField(blank=True, null=True, choices=CODES_CHOICES)
    merchant_id = models.CharField(max_length=100, blank=True, null=True, default='')
    lender = models.ForeignKey('Lender', on_delete=models.PROTECT)

    def __str__(self):
        return "%s (%s)" % (self.name, self.merchant_id)

    def get_bank_name(self):
        for i in self.CODES_CHOICES:
            if i[0] == self.code:
                return i[1]
        return 'no-bank-name'


class Terminal(extend.TrackModel):
    class Meta:
        verbose_name = "ترمینال"
        verbose_name_plural = "ترمینال‌ها"

    TYPE_POS = 1
    TYPE_IPG = 2
    TYPE_COUNTER = 8
    # TYPE_DEPOSIT = 9
    # TYPE_WITHDRAW = 10
    TYPE_ID_CHOICES = (
        (TYPE_POS, 'POS'),
        (TYPE_IPG, 'IPG'),
        (TYPE_COUNTER, 'COUNTER'),
        # (TYPE_DEPOSIT, 'DEPOSIT'),
        # (TYPE_WITHDRAW, 'WITHDRAW'),
    )

    type_id = models.IntegerField(choices=TYPE_ID_CHOICES)
    bank = models.ForeignKey('Bank', on_delete=models.PROTECT)
    desc = models.CharField(max_length=100, default='', blank=True)
    terminal_id = models.CharField(max_length=100, blank=True, default='')
    data = JSONField(default=dict, editable=False)

    # branch = models.ForeignKey('sales.Branch', blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return "%s مرچانت (%s) ترمینال (%s) نوع (%s)" % (
            self.bank.name, self.bank.merchant_id, self.terminal_id, self.get_type_label())

    def get_type_label(self):
        for i in self.TYPE_ID_CHOICES:
            if i[0] == self.type_id:
                return i[1]
        return 'none'
