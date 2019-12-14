# Admin site models.

from django.contrib import admin

from submissions import models


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    list_display = ['name', 'start_date', 'end_date', 'active', 'stage']
    list_filter = ['start_date', 'end_date', 'active']
    list_editable = ['active', 'stage']


@admin.register(models.Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'
    list_display = ['__str__', 'event', 'user']
    list_filter = ['event']


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['game', 'event', 'user', 'status']
    list_filter = ['event', ]


# Remaining models that don't need a custom admin handler.
admin.site.register(models.Profile)
admin.site.register(models.SubmissionCategory)
