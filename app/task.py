from celery import shared_task
from . models import Booking, TaskOrder
from django.utils import timezone
from django.db.models import Q


@shared_task
def stadium_time_checker():
    time = timezone.now() - timezone.timedelta(minutes=2)
    books = Booking.objects.filter(Q(start_time__gte=time) & Q(end_time__lte=time) & Q(status='Pending'))
    for book in books:
        book.status = 'Finished'
        book.is_busy = False
        task_order = TaskOrder.objects.get(id=book.task_order.first().id)
        task_order.periodic_task.delete()
        task_order.delete()
        book.save()
    return 'Done'