# apps/detaliu_registras/templatetags/form_filters.py

from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Prideda CSS klasę prie formos lauko HTML widget'o.
    Naudojama šablone: {{ field|add_class:"my-class" }}
    """
    return field.as_widget(attrs={"class": css_class})
