# core/templatetags/instance_of.py
from django import template

register = template.Library()

@register.filter
def instance_of(value, class_name):
    return value.__class__.__name__ == class_name
