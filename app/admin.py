from django.contrib import admin
from .models import Users, Stadium, Booking

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    pass

@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    pass

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    pass