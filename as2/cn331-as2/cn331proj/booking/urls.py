from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path("mine/", views.mine, name="mine"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("signup/", views.signup, name="signup"),
    path("staff/bookings/", views.admin_bookings, name="admin_bookings"),
]
