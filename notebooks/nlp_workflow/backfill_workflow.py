# Databricks notebook source
from datetime import UTC, datetime, timedelta

from nlp_inference.config import NLP_BACKFILL_TABLE_NAME, NLP_OUTPUT_TABLE_NAME

# COMMAND ----------

iterations = 6  # from 2022-06-01 to 2023-06-01

start = datetime(2022, 6, 1).astimezone(UTC).date()
end = datetime(2023, 6, 1).astimezone(UTC).date()
total_days = (end - start).days

interval = total_days // (
    iterations
)  # We divide by (iterations - 1) because we need (iterations - 1) intervals to obtain iterations
dates = [start + timedelta(days=interval * i) for i in range(iterations)] + [end]
date_ranges = []
for i in range(iterations):
    if i == 0:
        date_ranges.append((dates[i], dates[i + 1]))
    else:
        date_ranges.append((dates[i] + timedelta(days=1), dates[i + 1]))

spark.sql(f"TRUNCATE TABLE {NLP_BACKFILL_TABLE_NAME}")

for start, end in date_ranges:
    dbutils.notebook.run("data_ingestion/data_ingestion", 0, {"start": start, "end": end, "backfill": "true"})
    dbutils.notebook.run("nlp_inference/nlp_inference", 0)
    df_output = spark.table(NLP_OUTPUT_TABLE_NAME)
    df_output.write.insertInto(NLP_BACKFILL_TABLE_NAME)
