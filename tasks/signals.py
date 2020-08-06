from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, pre_save
from tasks.models import Task, ExtraComment


@receiver(post_save, sender=Task)
def task_state_changed(sender, instance, created=False, update_fields=None,  **kwargs):
    if created:
        return
    update_fields = kwargs.get('update_fields', {})
    print('update_fields.get("task_state")', update_fields.get('task_state'))
    print('task_state_changed', instance, instance.task_state, created, update_fields)
