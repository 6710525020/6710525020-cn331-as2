from django.test import TestCase, Client
from django.urls import reverse
from .models import Room,Booking
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)
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

        with self.assertRaisesMessage(Exception, "This time slot overlaps with another booking."):
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
        # one user can only booking one time per room
        now = timezone.now()
        booking1 = Booking(room=self.room,user=self.user1,start_time= now + timedelta(minutes=10),end_time= now + timedelta(minutes=50))

        booking1.full_clean()
        booking1.save()

        booking2 = Booking(room=self.room,user=self.user1,start_time=now + timedelta(hours=1, minutes=10),end_time=now + timedelta(hours=2))
        with self.assertRaisesMessage(ValidationError, "You already have an active or upcoming booking for this room."):
            booking2.save()

    def test_room_required(self):
        # must have room id
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking = Booking(user=self.user2,start_time=start_time,end_time=end_time)
        with self.assertRaisesMessage(Exception, "Room is required for booking"):
            booking.clean()

    def test_user_required(self):
        # must have user id
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking = Booking(room=self.room,start_time=start_time,end_time=end_time)
        with self.assertRaisesMessage(Exception, "User is required for booking"):
            booking.clean()

    def test_index_status_code(self):
        # test first page
        c = Client()
        resp = c.get(reverse("index"))
        self.assertEqual(resp.status_code,200)
        self.assertIn("room", resp.context)
        self.assertGreaterEqual(resp.context["room"].count(),1)    

    def test_room_detail_invalid(self):
        # test room detail
        c = Client()
        resp = c.get(reverse("room_detail", args=[999999]))
        self.assertEqual(resp.status_code, 404)

    def test_mine_booking(self):
        # show all user booking
        c = Client()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        Booking(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)
        Booking(room=self.room,user=self.user2,start_time=start_time,end_time=end_time)

        c.login(username="jigsaw", password="123456")
        resp = c.get(reverse("mine"))
        self.assertEqual(resp.status_code, 200)
        bookings = resp.context.get("bookings")
        self.assertTrue(all(b.user == self.user1 for b in bookings))

    def test_cancle_booking_owner_only(self):
        # owner can cancle booking
        c = Client()
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        booking = Booking(room=self.room,user=self.user1,start_time=start_time,end_time=end_time)
        c.login(username="jigsaw", password="123456")
        resp = c.post(reverse("cancle_booking", args=[booking.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Booking.objects.filter(id = booking.id).exists())

        # other try to cancle booking
        booking2 = Booking(room=self.room,user=self.user2,start_time=start_time,end_time=end_time)
        resp2 = c.post(reverse("cancle_booking", args=[booking2.id]))
        self.assertEqual(resp2.status_code, 404)
