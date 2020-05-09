from django.contrib import admin
from .util.extend import TrackModelAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from .models import Confirm, MobileTemp, UserMeta


# Register your models here.

def action_flag(obj):
    return "add" if obj.action_flag == ADDITION else ("change" if obj.action_flag == CHANGE else "delete")


def change_message(obj):
    return "add" if obj.action_flag == ADDITION else ("change" if obj.action_flag == CHANGE else "delete")


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', action_flag, 'change_message', 'user')


class MobileTempAdmin(admin.ModelAdmin):
    list_display = ('number', 'ip')


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Confirm)
admin.site.register(MobileTemp, MobileTempAdmin)
admin.site.register(UserMeta)
