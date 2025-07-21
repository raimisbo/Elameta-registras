from django import template

register = template.Library()

@register.inclusion_tag('snippets/uzklausa_blokas.html')
def rodyti_uzklausa(uzklausa):
    return {'uzklausa': uzklausa}