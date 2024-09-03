source {% if expr.operator == "not_in" %}NOT {% endif %}IN ({% for src in expr.value -%}
    '{{src.name}}'{% if not loop.last %}, {% endif %}
{%- endfor %})