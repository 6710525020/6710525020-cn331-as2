from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from .models import Room, Booking
from .forms import BookingForm
from django.contrib.admin.views.decorators import staff_member_required


def index(request):
    rooms = Room.objects.all()
    return render(request, "booking/index.html", {"rooms": rooms})


def room_detail(request, room_id):
    """Allow anyone to view; require login to submit a booking."""
    room = get_object_or_404(Room, pk=room_id)
    bookings = Booking.objects.filter(room=room)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        instance = Booking(room_id=room.id, user_id=request.user.id)
        form = BookingForm(request.POST, instance=instance)
        if form.is_valid():
            try:
                form.save()
                return redirect("room_detail", room_id=room.id)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        instance = Booking(room_id=room.id, user_id=request.user.id if request.user.is_authenticated else None)
        form = BookingForm(instance=instance)

    return render(request, "booking/room_detail.html", {
        "room": room,
        "bookings": bookings,
        "form": form
    })


@login_required
def mine(request):
    my_bookings = Booking.objects.filter(user=request.user).select_related("room")
    return render(request, "booking/mine.html", {"bookings": my_bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    booking.delete()
    return redirect("mine")


def signup(request):
    """Simple user self-registration."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("index")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

@staff_member_required
def admin_bookings(request):
    qs = Booking.objects.select_related("room", "user").order_by("-start_time")

    room_id = request.GET.get("room")
    username = request.GET.get("user")

    if room_id:
        qs = qs.filter(room_id=room_id)
    if username:
        qs = qs.filter(user__username__icontains=username)

    return render(request, "booking/admin_bookings.html", {
        "bookings": qs,
        "rooms": Room.objects.all(),
        "room_selected": room_id or "",
        "username_q": username or "",
    })