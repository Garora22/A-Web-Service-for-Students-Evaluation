from django.contrib import admin
from .models import Query, QueryMessage


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'course', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'course', 'created_at']
    search_fields = ['title', 'student__username', 'student__first_name', 'student__last_name']
    date_hierarchy = 'created_at'


@admin.register(QueryMessage)
class QueryMessageAdmin(admin.ModelAdmin):
    list_display = ['query', 'sender', 'message_preview', 'created_at']
    list_filter = ['created_at', 'sender__role']
    search_fields = ['message', 'sender__username']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
