import argparse
import json
import tomllib
from os import environ
from subprocess import run

import boto3


def main():
    parser = argparse.ArgumentParser(
        "rdsconnect.py",
        description="Injects RDS connection parameters into another command via environment variables. Configured via PEP 518 pyproject.toml tool table.",
        usage="rdsconnect.py [-h] --rdsprofile RDSPROFILE command [arguments]",
    )
    parser.add_argument(
        "--rdsprofile",
        required=True,
        help='RDS Connect profile to use. Should include "aws_profile" key for AWS Credential Profile and "rds_id" key for RDS instance identifier.',
    )
    args, command_args = parser.parse_known_args()

    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)["tool"]["rdsconnect"]

    if len(command_args) == 0:
        msg = "No subcommand passed in!"
        raise ValueError(msg)
    if command_args[0] not in config["interface"]:
        msg = f"RDS Connect interface for command '{command_args[0]}' not found!"
        raise ValueError(msg)
    if args.rdsprofile not in config["profile"]:
        msg = f"RDS Connect profile '{args.rdsprofile}' not found!"
        raise ValueError(msg)

    command_interface = config["interface"][command_args[0]]
    rds_profile = config["profile"][args.rdsprofile]
    session = boto3.Session(profile_name=rds_profile["aws_profile"])
    rds_client = session.client("rds")

    # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds/client/describe_db_instances.html
    db_description = rds_client.describe_db_instances(DBInstanceIdentifier=rds_profile["rds_id"])["DBInstances"][0]
    secret_arn = db_description["MasterUserSecret"]["SecretArn"]
    secrets_client = session.client("secretsmanager")
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(secret_response["SecretString"])

    # Extracted connection parameters
    hostname = db_description["Endpoint"]["Address"]
    port = db_description["Endpoint"]["Port"]
    jdbc_url = f"jdbc:postgresql://{hostname}:{port}/?sslmode=allow"
    username = secret["username"]
    password = secret["password"]

    # Populate specified environment variables
    command_env = {}
    for env_var, python_var in command_interface.items():
        command_env[env_var] = str(locals()[python_var])

    # Run subcommand with any additional arguments
    # Pass in local process environment updated with specified environment variables
    run(command_args, env=environ | command_env, check=False)


if __name__ == "__main__":
    main()
