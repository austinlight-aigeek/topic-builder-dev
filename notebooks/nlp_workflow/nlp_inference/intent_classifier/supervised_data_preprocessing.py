# Databricks notebook source
import numpy as np
import pandas as pd
from config import (
    PREPROCESSED_TRAINING_DATA_TABLE,
    PREPROCESSED_VALIDATION_DATA_TABLE,
    RAW_DATA_TABLE,
    TRAIN_SIZE,
)
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.functions import min as f_min

# Set seed for reproducibility
SEED = 42
np.random.seed(SEED)

# COMMAND ----------


@pandas_udf("string")
def extract_first_intent(intent_types: pd.Series) -> pd.Series:
    """
    Get the first intent type where there are more than one intent type in "intent_type.

    There are sentences with more than one type of intention, for example:
    0063x00001ZwjnSAAR|information-request;request|How would getting your degree change your current situation?

    We prioritize the intent type from left to right.
    """
    return intent_types.str.split(";").str[0]


# COMMAND ----------

df_input = spark.table(RAW_DATA_TABLE).select(
    col("ID").alias("id"),
    col("INTENT_TYPE").alias("intent_type"),
    col("SENTENCE_TEXT").alias("sentence_text"),
)
df_input = df_input.filter(col("INTENT_TYPE").isNotNull())
df_input = df_input.dropDuplicates(["sentence_text"])
df_input = df_input.withColumn("label", extract_first_intent("intent_type"))

# COMMAND ----------

"""The distribution label is:
statement              1622603
request                 119955
action-request          40268
information-request      33480
yes-no-question          8812

So we will sample based on the minimum count of these categories. Reason: We want balanced data, reduce overfitting of the majority class.
"""

min_count = df_input.groupBy("label").count().agg(f_min("count")).collect()[0][0]
df_input = df_input.groupBy("label").applyInPandas(
    lambda pdf: pdf.sample(min_count, random_state=SEED), schema=df_input.schema
)

# COMMAND ----------

df_input.groupBy("label").count().show()

# COMMAND ----------

# Split training and validation
df_train, df_val = df_input.randomSplit(weights=[TRAIN_SIZE, 1 - TRAIN_SIZE], seed=SEED)

# COMMAND ----------

df_train.write.format("delta").mode("overwrite").option("inferSchema", True).option(
    "overwriteSchema", True
).saveAsTable(PREPROCESSED_TRAINING_DATA_TABLE)

df_val.write.format("delta").mode("overwrite").option("inferSchema", True).option("overwriteSchema", True).saveAsTable(
    PREPROCESSED_VALIDATION_DATA_TABLE
)
