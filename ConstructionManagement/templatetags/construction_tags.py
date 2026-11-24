from django import template

register = template.Library()


@register.filter
def get_item(obj, key):
    """Return an object attribute by name, safely."""
    return getattr(obj, key, "")
