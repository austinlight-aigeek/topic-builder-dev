# Databricks notebook source
import sys

sys.path.append("../../../src/app")
from json import loads

import jinja2
from expr.nodes import Group
from sql.query import generate_sparksql_topics

# COMMAND ----------

existing_records = spark.table("applied_machine_learning.droptopicanalysis_dev.topic_dataset").drop("topics")
new_records = spark.table("applied_machine_learning.droptopicanalysis_dev.nlp_output")
all_records = existing_records.union(new_records).drop_duplicates(["source", "source_id", "sentence_pos"])

all_records.createOrReplaceTempView("records")

# COMMAND ----------

topics = spark.table("applied_machine_learning.droptopicanalysis_dev.rds_ruleset").collect()

topics = [t for t in topics if t.is_active]

# Validate using Pydantic models before rendering
topics = [(t.name, Group.model_validate(loads(t.expression)).model_dump()) for t in topics]

topic_sqls, parameters = await generate_sparksql_topics(topics, spark)

# COMMAND ----------

final_sql_template = jinja2.Template("""
SELECT *,
array_compact(array({% for sql in topic_sqls %}{{sql}}{% if not loop.last %},{% endif %}{% endfor %})) topics
FROM records
""")

# COMMAND ----------

final_sql = final_sql_template.render(topic_sqls=topic_sqls)

# COMMAND ----------

final_df = spark.sql(final_sql, parameters)

# COMMAND ----------

final_df.write.mode("overwrite").saveAsTable("applied_machine_learning.droptopicanalysis_dev.topic_dataset")
