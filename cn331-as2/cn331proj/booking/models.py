from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

class Room(models.Model):
    name = models.CharField(max_length=100)     
    capacity = models.IntegerField(default=0)      
    max_hours = models.IntegerField(default=1)       
    status = models.CharField(max_length=20, default="AVAILABLE")
    image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} → {self.room.name} ({self.start_time} ~ {self.end_time})"

    def clean(self):
        if not self.start_time or not self.end_time:
            raise ValidationError("Start time and end time are required.")
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        if not self.room_id:
            raise ValidationError("Room is required for booking.")
        if not self.user_id:
            raise ValidationError("User is required for booking.")

        duration = self.end_time - self.start_time
        if duration > timedelta(hours=self.room.max_hours):
            raise ValidationError(f"You can only book up to {self.room.max_hours} hour(s) per booking.")

        if getattr(self.room, "status", "AVAILABLE") != "AVAILABLE":
            raise ValidationError("This room is currently unavailable for booking.")

        overlap_exists = Booking.objects.filter(
            room_id=self.room_id
        ).exclude(pk=self.pk).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exists()
        if overlap_exists:
            raise ValidationError("This time slot overlaps with another booking.")

        now = timezone.now()
        already_has_active_or_future = Booking.objects.filter(
            room_id=self.room_id,
            user_id=self.user_id,
            end_time__gte=now,        
        ).exclude(pk=self.pk).exists()
        if already_has_active_or_future:
            raise ValidationError(
                "You already have an active or upcoming booking for this room."
            )
        
    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
