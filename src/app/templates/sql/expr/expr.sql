{%- if expr.id == 'Group' -%}
    {% include "_Group.sql" %}
{%- elif expr.id == 'Source' -%}
    {% include "_Source.sql" %}
{%- elif expr.id == 'Sentiment' -%}
    {% include "_Sentiment.sql" %}
{%- elif expr.id == 'Intent' -%}
    {% include "_Intent.sql" %}
{%- elif expr.id == 'Lemma' -%}
    {% include "_Lemma.sql" %}
{%- elif expr.id == 'Regex' -%}
    {% include "_Regex.sql" %}    
{%- elif expr.id == 'Similarity' -%}
    {% include "_Similarity.sql" %}
{%- elif expr.id == 'Date' -%}
    {% include "_Date.sql" %}

{#- Error out on unrecognized expr op #}
{%- else %}{{0/0}}{% endif %}