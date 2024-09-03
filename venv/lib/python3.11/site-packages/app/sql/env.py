import os

import jinja2
from sentence_transformers import SentenceTransformer
from sql.filters import (
    cos_sim_udf_sparksql,
    identifier_postgresql,
    identifier_sparksql,
    literal_postgresql,
    literal_sparksql,
)

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

dir_path = os.path.dirname(os.path.realpath(__file__))
sql_loader = jinja2.FileSystemLoader([f"{dir_path}/../templates/sql", f"{dir_path}/../templates/sql/expr"])


def prepare_postgresql_env(**ctx):
    env = jinja2.Environment(loader=sql_loader, enable_async=True)  # noqa: S701. SQL does not need HTML escaping.
    env.filters["identifier"] = identifier_postgresql
    env.filters["literal"] = literal_postgresql
    env.filters["embed"] = embedder.encode
    env.globals.update(**ctx, engine="postgresql")
    return env


def prepare_sparksql_env(**ctx):
    env = jinja2.Environment(loader=sql_loader, enable_async=True)  # noqa: S701. SQL does not need HTML escaping.
    env.filters["identifier"] = identifier_sparksql
    env.filters["literal"] = literal_sparksql
    env.filters["embed"] = embedder.encode
    env.filters["cos_sim_udf"] = cos_sim_udf_sparksql
    env.globals.update(**ctx, engine="sparksql")
    return env
