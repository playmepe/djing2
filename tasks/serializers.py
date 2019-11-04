from django.contrib.auth import get_user_model
from rest_framework import serializers
from tasks import models


UserProfile = get_user_model()


class ChangeLogModelSerializer(serializers.ModelSerializer):
    who_name = serializers.CharField(source='who.get_full_name', read_only=True)

    class Meta:
        model = models.ChangeLog
        fields = '__all__'


class TaskModelSerializer(serializers.ModelSerializer):
    author_full_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_uname = serializers.CharField(source='author.username', read_only=True)
    priority_name = serializers.CharField(source='get_priority_display', read_only=True)
    time_diff = serializers.CharField(source='get_time_diff', read_only=True)
    customer_address = serializers.CharField(source='customer.get_address', read_only=True)
    customer_full_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_uname = serializers.CharField(source='customer.username', read_only=True)
    customer_group = serializers.IntegerField(source='customer.group_id', read_only=True)
    comment_count = serializers.IntegerField(source='extracomment_set.count', read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(many=True, queryset=UserProfile.objects.only('pk', 'username', 'fio'))
    state_str = serializers.CharField(source='get_state_display', read_only=True)
    mode_str = serializers.CharField(source='get_mode_display', read_only=True)
    time_of_create = serializers.DateTimeField(read_only=True)

    class Meta:
        model = models.Task
        fields = '__all__'


class ExtraCommentModelSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.pk', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_avatar = serializers.CharField(source='author.get_avatar_url', read_only=True)

    class Meta:
        model = models.ExtraComment
        exclude = ('author',)
