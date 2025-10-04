from django.test import TestCase, Client
from django.urls import reverse
from .models import Room,Booking
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

# Create your tests here.

class bookingTest(TestCase):

    def setUp(self):
        # create booking
        self.user1 = User.objects.create_user(username="jigsaw", password="123456")
        self.user2 = User.objects.create_user(username="punch", password="789123")

        self.room = Room.objects.create(name="library1", capacity=10, max_hours=1, status="AVAILABLE" )
    
    def test_booking_str(self):
        # check username and room's name
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)
        booking = Booking.objects.create(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)
        text = str(booking)
        self.assertIn(self.user1.username, text)
        self.assertIn(self.room.name, text)

    def test_clean_valid_booking(self):
        # check booking time
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking = Booking(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)

        try:
            booking.clean()
        except Exception as e:
            self.fail(f"Booking.clean() raised unexpectedly: {e}")

    def test_end_before_start(self):
        # check that start time is before end time
        start_time = timezone.now() - timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking= Booking(room=self.room,user=self.user2,start_time=start_time,end_time=end_time)
        with self.assertRaisesMessage(Exception,"End time must be after start time."):
            booking.clean()

    def test_clean_overlap_booking(self):
        # check overlapping booking time
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        Booking.objects.create(room=self.room, user=self.user1,start_time=start_time,end_time=end_time)

        overlap_start = start_time + timedelta(minutes=30)
        overlap_end = end_time + timedelta(minutes=30)

        with self.assertRaisesMessage(Exception, "Overlaps with another booking"):
            Booking.objects.create(room=self.room,user=self.user1,start_time=overlap_start,end_time=overlap_end)
    
    def test_cannot_exceed_max_hours(self):
        # check that time booking cannot more than max_hours(1 hour)
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=5)
        booking = Booking(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)
        with self.assertRaisesMessage(Exception, "You can only book up to"):
            booking.clean()

    def test_room_status(self):
        # check status room that available or unavailable
        self.room.status = "UNAVAILABLE"
        self.room.save()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking = Booking(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)
        with self.assertRaisesMessage(Exception, "This room is currently unavailable for booking."):
            booking.clean()

    def test_booking_per_user_per_room(self):
        # one user can only booking one time per room\
        now = timezone.now()
        Booking(room=self.room,user=self.user1,start_time=now + timedelta(minutes=10),end_time=now + timedelta(minutes=1))
        booking2 = Booking(room=self.room,user=self.user1,start_time=now + timedelta(hours=1, minutes=10),end_time=now + timedelta(hours=2))

        with self.assertRaisesMessage(Exception, "You already have an active or upcoming booking for this room."):
            booking2.save()