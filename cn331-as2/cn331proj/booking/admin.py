from django.contrib import admin
from .models import Room, Booking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "max_hours", "status")
    list_filter = ("status",)
    search_fields = ("name",)
    fields = ("name", "capacity", "max_hours", "status", "image")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "start_time", "end_time")
    list_filter = ("room", "user")
    search_fields = ("room__name", "user__username")
