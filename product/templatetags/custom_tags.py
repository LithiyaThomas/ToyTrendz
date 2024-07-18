from django import template

register = template.Library()

@register.filter
def range_filter(value):
    return range(value)

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument.
    """
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ''

