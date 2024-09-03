{% if engine == "postgresql" -%}
regexp_match(sentence_text, {{expr.value|literal}}) IS NOT NULL
{%- else -%}
regexp(sentence_text, {{expr.value|literal}})
{%- endif %}