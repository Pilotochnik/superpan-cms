from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Получить значение из словаря по ключу"""
    return dictionary.get(key, [])
