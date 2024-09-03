# Databricks notebook source
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import torch
from config import (
    CANDIDATE_LABELS_SENTIMENT,
    NLP_INPUT_TABLE_NAME,
    NLP_OUTPUT_TABLE_NAME,
    pipeline,
    sentence_transformer,
)
from intent_classifier.config import REGISTERED_MODEL_NAME
from mlflow.pyfunc import spark_udf
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.types import ArrayType, StringType, StructField, StructType
from udf import extract_semantic_entities

# COMMAND ----------

nlp_input = spark.table(NLP_INPUT_TABLE_NAME)

# COMMAND ----------

nlp_output = pipeline.fit(nlp_input).transform(nlp_input)

# COMMAND ----------

entities_schema = ArrayType(
    StructType(
        [
            StructField("agent", ArrayType(StringType())),
            StructField("lemma", ArrayType(StringType())),
            StructField("theme", ArrayType(StringType())),
            StructField("goal", ArrayType(StringType())),
            StructField("beneficiary", ArrayType(StringType())),
            StructField("entities_related_to_lemma", ArrayType(StringType())),
        ]
    )
)


@pandas_udf("string")
def get_sentiment(result: pd.Series) -> pd.Series:
    """Get the the sentiment with the maximum probability"""
    return pd.DataFrame(result.apply(lambda x: x[0].get("metadata")).tolist(), dtype=float)[
        CANDIDATE_LABELS_SENTIMENT
    ].idxmax(axis=1)


get_intents = spark_udf(
    spark,
    model_uri=f"models:/{REGISTERED_MODEL_NAME}/Production",
    result_type="intent_type STRING, intent_score FLOAT",
)


@pandas_udf(entities_schema)
def get_semantic_entity_parser(sentence_text: pd.Series) -> pd.Series:
    """
    Parse sentence_text, get agent, lemma, topic, goal adn beneficiary entitites.
    """
    with ProcessPoolExecutor() as executor:
        results = executor.map(extract_semantic_entities, sentence_text, chunksize=1)
    return pd.Series([*results])


BATCH_SIZE = 1024
MIN_SENTENCE_WORDS = 4


@pandas_udf("array<float>")
def get_vector_embs(sentences: pd.Series) -> pd.Series:
    bad_sentences = sentences.str.split().str.len() < MIN_SENTENCE_WORDS  # pd.Series[bool]
    embeds = sentence_transformer.encode(sentences=sentences, batch_size=BATCH_SIZE)  # np.ndarray(2D)
    torch.cuda.empty_cache()
    embeds[bad_sentences, :] = 0
    return pd.Series([*embeds])  # pd.Series[np.ndarray(1D)]


# COMMAND ----------

nlp_output = (
    nlp_output.withColumn("sentiment", get_sentiment("label"))
    .withColumn("intent", get_intents("sentence_text"))
    .withColumn("semantic_entities", get_semantic_entity_parser("sentence_text"))
    .withColumn("intent_type", col("intent").intent_type)
    .withColumn("intent_score", col("intent").intent_score)
    .withColumn("agent", col("semantic_entities")[0].agent)
    .withColumn("lemma", col("semantic_entities")[0].lemma)
    .withColumn("theme", col("semantic_entities")[0].theme)
    .withColumn("goal", col("semantic_entities")[0].goal)
    .withColumn("beneficiary", col("semantic_entities")[0].beneficiary)
    .withColumn(
        "entities_related_to_lemma",
        col("semantic_entities")[0].entities_related_to_lemma,
    )
    .withColumn("embedding", get_vector_embs("sentence_text"))
    .drop("document", "token", "label", "intent", "semantic_entities")
)

display(nlp_output)

# COMMAND ----------

nlp_output.write.format("delta").mode("overwrite").option("inferSchema", True).option(
    "overwriteSchema", True
).saveAsTable(NLP_OUTPUT_TABLE_NAME)
