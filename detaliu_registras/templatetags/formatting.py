# Failas: detaliu_registras/templatetags/formatting.py
# Paskirtis: Pagalbiniai šablono filtrai datoms iš intervalų/sąrašų/stringų:
# - {{ value|date_start }} -> paima "pradžios" datą (iš Date/DateTime/Range/masyvo/teksto)
# - {{ value|date_end }}   -> paima "pabaigos" datą (jei reikės rodyti "iki")
#
# Šiuos filtrus gali naudoti kartu su Django |date:"Y-m-d".
# Jei filtras grąžina string'ą "YYYY-MM-DD", |date neperformatuos, bet tai OK.

from datetime import date, datetime
import re
from django import template

register = template.Library()


def _coerce_first_date(value):
    """
    Grąžina pirmą datą iš įvairių tipų:
    - date/datetime -> pati reikšmė
    - Postgres Range (turi .lower) -> lower
    - sąrašas/tuplas -> elementas [0]
    - string -> pirmas YYYY-MM-DD pattern'as
    Kitaip grąžina originalą (šablone dar prasisuks |date).
    """
    # date / datetime
    if isinstance(value, (date, datetime)):
      return value

    # Postgres Range: turi .lower
    lower = getattr(value, "lower", None)
    if isinstance(lower, (date, datetime)):
      return lower

    # sąrašas / tuplas
    if isinstance(value, (list, tuple)) and value:
      v0 = value[0]
      if isinstance(v0, (date, datetime)):
        return v0
      if isinstance(v0, str):
        m = re.search(r"\d{4}-\d{2}-\d{2}", v0)
        if m:
          return m.group(0)

    # string: paimam pirmą YYYY-MM-DD
    if isinstance(value, str):
      m = re.search(r"\d{4}-\d{2}-\d{2}", value)
      if m:
        return m.group(0)

    return value


def _coerce_second_date(value):
    """
    Grąžina antrą datą (naudinga, jei kada reikės 'iki'):
    - Postgres Range: .upper
    - sąrašas/tuplas: [1]
    - string: antras YYYY-MM-DD
    Kitais atvejais grąžina originalą.
    """
    upper = getattr(value, "upper", None)
    if isinstance(upper, (date, datetime)):
      return upper

    if isinstance(value, (list, tuple)) and len(value) > 1:
      v1 = value[1]
      if isinstance(v1, (date, datetime)):
        return v1
      if isinstance(v1, str):
        m = re.search(r"\d{4}-\d{2}-\d{2}", v1)
        if m:
          return m.group(0)

    if isinstance(value, str):
      all_dates = re.findall(r"\d{4}-\d{2}-\d{2}", value)
      if len(all_dates) >= 2:
        return all_dates[1]

    return value


@register.filter
def date_start(value):
    """Paimti pirmą datą iš galimos intervalo/masyvo/stringo reikšmės."""
    return _coerce_first_date(value)


@register.filter
def date_end(value):
    """Paimti antrą datą (intervalo pabaigą), jei reikėtų rodyti „iki“."""
    return _coerce_second_date(value)
