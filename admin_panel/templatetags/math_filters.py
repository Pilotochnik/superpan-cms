from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def div(value, divisor):
    """Деление чисел"""
    try:
        if divisor == 0:
            return 0
        return float(value) / float(divisor)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, multiplier):
    """Умножение чисел"""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, subtractor):
    """Вычитание чисел"""
    try:
        return float(value) - float(subtractor)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Вычисление процента"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
