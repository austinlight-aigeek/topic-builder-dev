import json
import os
from os import getenv

import boto3

AWS_SECRET_ID = "/MLOps/mlops-nlp-topic-builder"  # noqa: S105. This is a path to the AWS secret, not a secret itself

# Fetch configuration from AWS if it was not passed in as environment variables
if getenv("POSTGRES_USER") is None:
    client = boto3.client("secretsmanager")
    secret_str = client.get_secret_value(SecretId=AWS_SECRET_ID)["SecretString"]
    secret = json.loads(secret_str)

    # Update environment variables that are in the AWS secret and not already defined locally
    for key, value in secret.items():
        os.environ[key] = getenv(key, value)
