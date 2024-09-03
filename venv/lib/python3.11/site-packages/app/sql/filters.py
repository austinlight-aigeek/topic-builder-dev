# SQL translation filters
# Abstract away parameterization as PostgreSQL and Spark SQL handle it differently

import jinja2
import numpy as np


def identifier_postgresql(id_):
    # Format as quoted identifier
    # See https://www.postgresql.org/docs/16/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS
    return '"' + id_.replace('"', '""') + '"'


@jinja2.pass_environment
def identifier_sparksql(env, id_):
    # Use Spark SQL IDENTIFIER keyword with unnamed parameter marker
    # Build up our global list of parameters as we emit parameter markers
    # Databricks Runtime 13.3+
    env.globals["parameters"].append(id_)
    return "IDENTIFIER(?)"


@jinja2.pass_environment
def literal_postgresql(env, value):
    # psycopg uses "%s" as its placeholder
    env.globals["parameters"].append(value)
    return "%s"


@jinja2.pass_environment
def literal_sparksql(env, value):
    env.globals["parameters"].append(value)
    return "?"


@jinja2.pass_environment
def cos_sim_udf_sparksql(env, query_embed):
    # TODO: Test in Databricks

    # Lazy import so we don't need these libraries for the app
    import pandas as pd
    from pyspark.sql.functions import pandas_udf

    # Normalize query embedding
    norm_query_embed = query_embed / np.linalg.norm(query_embed)

    # REQUIREMENT: sentence embeddings have been normalized
    @pandas_udf("float")
    def cos_sim_udf(sent_embeds: pd.Series) -> pd.Series:
        matrix = np.stack(sent_embeds.values)
        scores = matrix @ norm_query_embed
        return pd.Series(scores)

    # Generate next UDF name using counter and increment
    counter = env.globals["udf_counter"]
    udf_name = f"cos_sim_udf_{counter}"
    env.globals["udf_counter"] += 1

    # Register this UDF in Spark context, then generate a call to the registered UDF in SQL
    env.globals["spark"].udf.register(udf_name, cos_sim_udf)
    return udf_name
