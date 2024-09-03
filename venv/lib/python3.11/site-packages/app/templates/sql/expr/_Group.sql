{% filter indent(width=2) %}{% if expr.not_ %}NOT {% endif %}(
{% for child in expr.rules -%}
    {% with expr = child -%}
        {% include "expr.sql" %}
    {%- endwith %}
    {%- if not loop.last %} {{expr.condition}}
{% endif %}
{%- endfor %}{% endfilter %}
)