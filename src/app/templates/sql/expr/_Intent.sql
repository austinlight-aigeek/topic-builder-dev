intent_type {% if expr.operator == "not_in" %}NOT {% endif %}IN ({% for src in expr.value -%}
    '{{src.value}}'{% if not loop.last %}, {% endif %}
{%- endfor %})