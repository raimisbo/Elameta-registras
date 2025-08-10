from django import template

register = template.Library()


@register.inclusion_tag("detaliu_registras/components/uzklausa_blokas.html")
def rodyti_uzklausa(uzklausa):
    return {"uzklausa": uzklausa}
