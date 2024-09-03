{% if engine == "postgresql" -%}
1 - (embedding <=> {{expr.text|embed|literal}}) {% if expr.operator == "greater" %}>{% else %}<{% endif %} {{expr.threshold|literal}}
{%- else -%}
{{expr.text|embed|cos_sim_udf}}(embedding) {% if expr.operator == "greater" %}>{% else %}<{% endif %} {{expr.threshold|literal}}
{%- endif %}