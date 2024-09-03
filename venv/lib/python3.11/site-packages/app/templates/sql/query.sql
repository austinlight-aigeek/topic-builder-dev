SELECT source, source_id, MIN(sentence_pos) AS sentence_pos, full_text AS full_text
FROM {{table}} 
JOIN (
    SELECT source AS fc_source, source_id AS fc_source_id, array_agg(sentence_text ORDER BY sentence_pos) AS full_text
    FROM {{table}} GROUP BY source, source_id) full_context
ON source = fc_source AND source_id = fc_source_id
WHERE {% include "expr/expr.sql" %}
GROUP BY source, source_id, full_text, createdatetime
ORDER BY createdatetime
LIMIT {{limit}}