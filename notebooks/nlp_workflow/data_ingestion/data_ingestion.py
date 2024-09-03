# Databricks notebook source
import html
import re
from datetime import UTC, datetime, timedelta

import pandas as pd
import pyspark.sql.functions as F  # noqa: N812. Importing functional module as F is a standard pattern.
from config import BOUNDS, NLP_INGESTION_TABLE_NAME
from pyspark.ml import PipelineModel
from pyspark.sql.types import ArrayType, IntegerType, StringType, StructField, StructType
from sparknlp.annotator import SentenceDetector
from sparknlp.base import DocumentAssembler

# COMMAND ----------

dbutils.widgets.text("start", "")
dbutils.widgets.text("end", "")
dbutils.widgets.dropdown("backfill", "false", ["true", "false"], "Select an option")

# COMMAND ----------

if dbutils.widgets.get("start") != "":
    start = datetime.strptime(dbutils.widgets.get("start"), "%Y-%m-%d").astimezone(UTC).date()
    end = datetime.strptime(dbutils.widgets.get("end"), "%Y-%m-%d").astimezone(UTC).date()
else:
    start = end = datetime.now(UTC).date() - timedelta(days=1)

enrollment_cutoff = start - timedelta(days=90)
backfill = dbutils.widgets.get("backfill").lower() == "true"

# COMMAND ----------


def unescape_html(value):
    return re.sub(r"\s+", " ", html.unescape(value).strip())


spark.udf.register("unescape_html", unescape_html, returnType=StringType())

# COMMAND ----------

pidm_emails_df = spark.sql(
    """
    WITH
    raw_emails AS ( -- Collect all emails from each row into array
      SELECT STUDENT_PIDM, ARRAY(EMAIL, WGU_EMAIL, DEFAULT_EMAIL, BUSINESS_EMAIL, HOME_EMAIL, GRADAPP_PRIMARY_NON_WGU_EMAIL) AS EMAILS FROM wgubi.vw_student_demographics
      WHERE STUDENT_PIDM IS NOT NULL  -- Ignore null PIDMs
    ), filtered_emails AS (  -- Get rid of null or empty emails
      SELECT STUDENT_PIDM, FILTER(EMAILS, E -> LEN(E) > 0) AS EMAILS FROM raw_emails
    ), exploded_email AS ( -- Break out each email/PIDM combination into its own row
      SELECT STUDENT_PIDM, EXPLODE(EMAILS) AS EMAIL FROM filtered_emails
    ), normalized_email AS ( -- Normalize in prepration for deduplication/join. Should match normalization on the other side of equijoins.
      SELECT STUDENT_PIDM, replace(lower(EMAIL), "@my.wgu.edu", "@wgu.edu") AS EMAIL FROM exploded_email
    )
    -- Drop any duplicate email -> PIDM mappings. This means each email shall map to at most one PIDM, and equijoins will produce at most one output row per input row.
    SELECT FIRST(STUDENT_PIDM) AS STUDENT_PIDM, EMAIL AS EMAIL FROM normalized_email
    GROUP BY EMAIL
  """
)
pidm_emails_df.createOrReplaceTempView("pidm_emails")

emails_with_pidms_df = spark.sql(
    """
    WITH email_clean AS (
      SELECT
        em_clean.ID,
        em_clean.CREATEDDATE,
        em_clean.HTMLBODY,
        em_clean.INCOMING,
        replace(lower(CASE WHEN INCOMING = 1 THEN em_clean.FROMADDRESS ELSE em_clean.TOADDRESS END), "@my.wgu.edu", "@wgu.edu") AS EMAIL -- Use the student's email address, according to INCOMING
      FROM wgubi.bi_e_emailmessage em_clean
      WHERE em_clean.CREATEDDATE BETWEEN :start AND :end
    )
    SELECT em.ID, em.CREATEDDATE, pe.STUDENT_PIDM, em.HTMLBODY, em.INCOMING
    FROM email_clean em
    INNER JOIN pidm_emails pe ON em.EMAIL = pe.EMAIL
""",
    {"start": start, "end": end},
)

# For debugging purposes. This may or may not be useful in actual pipelines
emails_with_pidms_cached = emails_with_pidms_df.collect()
emails_with_pidms_df = spark.createDataFrame(sc.parallelize(emails_with_pidms_cached))
emails_with_pidms_cached = None

emails_with_pidms_df.createOrReplaceTempView("emails_with_pidms")

# COMMAND ----------

if backfill:
    input_df = spark.sql(
        """
    -- First query determines the column names
    SELECT ID AS source_id, 'ENROLLMENT' AS source, CREATEDDATETIME__C AS createdatetime, PIDM__C AS pidm, 'Enrollment Note' AS type, unescape_html(regexp_replace(regexp_replace(THINGSTODISCUSSNOTES__C, '<[^>]*>', ' '), ' +', ' '))  AS data
    FROM wgubi.bi_o_opportunity
    WHERE CREATEDDATETIME__C BETWEEN :start AND :end
    AND LEN(THINGSTODISCUSSNOTES__C) > 0
    UNION ALL
    SELECT ID, 'MENTOR', CREATEDDATE, PIDM__C, TYPE__C, unescape_html(regexp_replace(regexp_replace(TEXT__C, '<[^>]*>', ' '), ' +', ' '))
    FROM wgubi.bi_w_wgustudentnotes__c
    WHERE CREATEDDATE BETWEEN :start AND :end
    AND TYPE__C != 'Mass Email' -- We're probably not interested in mass emails
    UNION ALL
    SELECT ID, 'EMAIL', CREATEDDATE, STUDENT_PIDM, CASE WHEN INCOMING = 1 THEN 'Email from Student' ELSE 'Email to Student' END, unescape_html(regexp_replace(regexp_replace(HTMLBODY, '<[^>]*>', ' '), ' +', ' '))
    FROM emails_with_pidms -- Date filtering handled in the view
    """,
        {"start": start, "end": end},
    )
else:
    input_df = spark.sql(
        """
    -- First query determines the column names
    SELECT ID AS source_id, 'ENROLLMENT' AS source, CREATEDDATETIME__C AS createdatetime, PIDM__C AS pidm, 'Enrollment Note' AS type, unescape_html(regexp_replace(regexp_replace(THINGSTODISCUSSNOTES__C, '<[^>]*>', ' '), ' +', ' '))  AS data
    FROM wgubi.bi_o_opportunity
    WHERE CREATEDDATETIME__C > :enrollment_cutoff AND LASTMODIFIEDDATE BETWEEN :start AND :end
    AND LEN(THINGSTODISCUSSNOTES__C) > 0
    UNION ALL
    SELECT ID, 'MENTOR', CREATEDDATE, PIDM__C, TYPE__C, unescape_html(regexp_replace(regexp_replace(TEXT__C, '<[^>]*>', ' '), ' +', ' '))
    FROM wgubi.bi_w_wgustudentnotes__c
    WHERE CREATEDDATE BETWEEN :start AND :end
    AND TYPE__C != 'Mass Email' -- We're probably not interested in mass emails
    UNION ALL
    SELECT ID, 'EMAIL', CREATEDDATE, STUDENT_PIDM, CASE WHEN INCOMING = 1 THEN 'Email from Student' ELSE 'Email to Student' END, unescape_html(regexp_replace(regexp_replace(HTMLBODY, '<[^>]*>', ' '), ' +', ' '))
    FROM emails_with_pidms -- Date filtering handled in the view
    """,
        {"start": start, "end": end, "enrollment_cutoff": enrollment_cutoff},
    )

# Force caching once table data has been read into memory
# Needed because source data comprises many gigabytes, and Spark keeps wanting to read the source tables, even when I use cache()
input_cached = input_df.collect()
input_df = (
    spark.createDataFrame(sc.parallelize(input_cached))
    .withColumn("createdatetime", F.to_timestamp(F.col("createdatetime")))
    .withColumn("pidm", F.col("pidm").cast(IntegerType()))
)
input_cached = None

display(input_df)

# COMMAND ----------

input_df.count()

# COMMAND ----------

# Overwrite columns as we go to minimize memory use
documenter = DocumentAssembler().setInputCol("data").setOutputCol("data")

sentencer = (
    SentenceDetector()
    .setInputCols("data")
    .setOutputCol("data")
    .setCustomBounds(BOUNDS)
    .setUseCustomBoundsOnly(True)
    .setExplodeSentences(False)
)

sd_pipeline = PipelineModel(stages=[documenter, sentencer])

# COMMAND ----------

sentence_df = sd_pipeline.transform(input_df)
display(sentence_df)

# COMMAND ----------

sentence_schema = ArrayType(
    StructType(
        [
            StructField("sentence_text", StringType(), True),
            StructField("sentence_pos", IntegerType(), True),
        ]
    )
)

MIN_SENTENCE_LENGTH = 11


def join_sentence(row):
    """
    The Current sentence boundary detection algorithm is based on detecting sentence boundaries using regular expressions (https://sparknlp.org/docs/en/annotators#sentencedetector). This algorithm produces some poor sentences such as broken sentences and very short sentence length.

    We should take care that texts that we convert into vectors have complete semantics, we should avoid incomplete sentences that lack meaning, or that they are very short.

    Join sentence engine:
      Join sentence according MIN_SENTENCE_LENGTH threshold.
    """
    if len(row) == 0:
        return None

    sentences_queue = [c["result"] for c in row]  # think this list as queue data structure
    new_sentences = []
    new_sentence_length = 0
    while len(sentences_queue) > 0:
        join_sentences = ""
        while new_sentence_length < MIN_SENTENCE_LENGTH and len(sentences_queue) > 0:
            sentence = sentences_queue.pop(0)
            new_sentence_length += len(sentence.split())
            join_sentences += sentence + ". "
        new_sentences.append(join_sentences.rstrip(". "))
        new_sentence_length = 0
    # Handle last sentence
    if len(new_sentences[-1].split()) < MIN_SENTENCE_LENGTH and len(new_sentences) > 1:
        sentence = new_sentences.pop(-1)
        new_sentences[-1] += ". " + sentence

    return [{"sentence_text": s, "sentence_pos": s_p} for s_p, s in enumerate(new_sentences)]


def parse_and_join_sentences(row: pd.Series) -> pd.Series:
    return row.apply(join_sentence)


parse_and_join_sentences_udf = F.pandas_udf(parse_and_join_sentences, returnType=sentence_schema)

# COMMAND ----------

final_df = (
    sentence_df.withColumn("data", parse_and_join_sentences_udf("data"))
    .withColumn("data", F.explode("data"))
    .withColumn("sentence_text", F.col("data").sentence_text)
    .withColumn("sentence_pos", F.col("data").sentence_pos)
    .drop("data")
)
display(final_df)

# COMMAND ----------

final_df.write.format("delta").mode("overwrite").option("inferSchema", True).option(
    "overwriteSchema", True
).saveAsTable(NLP_INGESTION_TABLE_NAME)
