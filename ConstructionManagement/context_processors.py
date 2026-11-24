"""Global template context for the construction management system."""

from .models import Notification


def global_context(request):
    notifications = Notification.objects.filter(audience__in=["ALL", "MANAGER", "SUPERVISOR"])[:8]
    return {
        "global_notifications": notifications,
        "unread_count": Notification.objects.filter(is_read=False).count(),
        "app_name": "Real Estate Builder",
    }
