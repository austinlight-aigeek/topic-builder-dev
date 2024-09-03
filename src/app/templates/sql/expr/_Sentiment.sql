sentiment {% if expr.operator == "not_in" %}NOT {% endif %}IN ({% for sent_val in expr.value -%}
    '{{sent_val.value}}'{% if not loop.last %}, {% endif %}
{%- endfor %})