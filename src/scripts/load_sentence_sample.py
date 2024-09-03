import argparse
from os import environ
from sys import exit

import psycopg
from databricks.connect import DatabricksSession
from sqlalchemy import URL

# Configure PostgreSQL connection
POSTGRES_USER = environ.get("POSTGRES_USER", "postgres")
POSTGRES_DB = environ.get("POSTGRES_DB", "postgres")
POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = environ.get("POSTGRES_PORT", 5432)
connection_string = URL.create(
    "postgresql", POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, int(POSTGRES_PORT), POSTGRES_DB
).render_as_string(hide_password=False)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        "load_sentence_sample.py", description="Populate sentence table in the NLP Topic Builder application"
    )
    parser.add_argument("-p", "--profile", default="wgu-prod", help="the databricks profile (default: wgu-prod)")

    args = parser.parse_args()

    spark = DatabricksSession.builder.profile(args.profile).getOrCreate()
    records = spark.table("applied_machine_learning.droptopicanalysis_dev.sample_dataset").collect()
    if not records:
        exit()

    with psycopg.connect(connection_string) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE sentence;")

        records = [tuple(value for value in record) for record in records]
        cur.executemany(
            """
                INSERT INTO sentence (source_id, source, createdatetime, pidm, type, sentence_text, sentence_pos, sentiment, intent_type, agent, lemma, theme, goal, beneficiary, entities_related_to_lemma, embedding)
                        VALUES(%s, %s, %s, %s, %s, %s,  %s, %s,  %s, %s,  %s, %s,  %s, %s,  %s, %s);
            """,
            records,
        )


if __name__ == "__main__":
    main()
