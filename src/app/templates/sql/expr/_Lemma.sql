{% if engine == "postgresql" -%}
lemma && ARRAY[
    {%- for term in expr.value.split(",") -%}
    {{term|literal}}
    {%- if not loop.last %}, {% endif %}
    {%- endfor -%}
]
{%- else -%}
arrays_overlap(lemma, array(
    {%- for term in expr.value.split(",") -%}
    {{term|literal}}
    {%- if not loop.last %}, {% endif %}
    {%- endfor -%}
))
{%- endif %}