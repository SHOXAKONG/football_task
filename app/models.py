from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

class Users(AbstractUser):
    ROLES = (
        ('Owner', 'OwnerStadium'),
        ('User', 'User'),
    )

    role = models.CharField(max_length=200, choices=ROLES, default='User')


class Stadium(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.CharField(max_length=70)
    longitude = models.CharField(max_length=70)
    address = models.TextField()
    contact = models.CharField(max_length=100)
    image = models.ImageField(upload_to='stadium_images/', blank=True, null=True)
    price = models.PositiveIntegerField()
    owner = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, related_name='stadium')

    def __str__(self):
        return self.name


STATUS = (
    ('Pending', 'Pending'),
    ('Canceled', 'Canceled'),
    ('Finished', 'Finished'),
)

def default_period_end():
    return timezone.now() + timedelta(hours=1)

class Booking(models.Model):
    phone_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=default_period_end)
    is_busy = models.BooleanField(default=True)
    status = models.CharField(choices=STATUS, max_length=255, default='Pending')
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name='booking')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.stadium} {self.start_time} - {self.end_time}"

    def save(self, *args, **kwargs):
        duration_in_seconds = (self.end_time - self.start_time).total_seconds()
        hours = duration_in_seconds / 3600

        self.total_price = self.stadium.price * hours
        super().save(*args, **kwargs)


class TaskOrder(models.Model):
    book = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='task_order')
    periodic_task = models.ForeignKey(PeriodicTask, on_delete=models.CASCADE)

    def __str__(self):
        return self.book.user.username