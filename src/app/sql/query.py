from sql.env import prepare_postgresql_env, prepare_sparksql_env


async def generate_postgresql_query(expr, limit=50):
    parameters = []
    env = prepare_postgresql_env(parameters=parameters, table="sentence", limit=limit)
    template = env.get_template("query.sql")
    sql = await template.render_async(expr=expr)
    return sql, tuple(parameters)


async def generate_sparksql_topics(
    topics: list[tuple[str, dict]],
    spark: "SparkContext",  # noqa: F821. SparkContext is defined within Databricks.
):
    sqls = []
    parameters = []
    env = prepare_sparksql_env(parameters=parameters, spark=spark, udf_counter=1)
    template = env.get_template("topic.sql")
    for name, expr in topics:
        sqls.append(await template.render_async(name=name, expr=expr))
    return sqls, parameters
