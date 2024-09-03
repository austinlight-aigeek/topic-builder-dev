import argparse
from getpass import getpass
from os import environ
from uuid import uuid4

import psycopg
from app.crypto import pwd_context
from sqlalchemy import URL

# Configure PostgreSQL connection
POSTGRES_USER = environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = environ.get("POSTGRES_PORT", 5432)
connection_string = URL.create(
    "postgresql", POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, int(POSTGRES_PORT)
).render_as_string(hide_password=False)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        "create_user.py", description="Creates a user in the NLP Topic Builder application"
    )
    parser.add_argument("-u", "--username", required=True, help="the login username of the user")
    parser.add_argument(
        "-s",
        "--superuser",
        action="store_true",
        default=False,
        help="whether this user should be a superuser (default: false)",
    )
    parser.add_argument(
        "-d",
        "--disabled",
        action="store_true",
        default=False,
        help="whether this user should be disabled (default: false)",
    )
    args = parser.parse_args()

    # Get password from user
    confirmed = False
    while not confirmed:
        password = getpass()
        password_confirm = getpass("Confirm password: ")
        if len(password) == 0:
            print("Please use a non-empty password.")
        elif password == password_confirm:
            confirmed = True
        else:
            print("Passwords do not match! Try again.")

    # The parameters to be passed to the INSERT statement
    id_ = uuid4()
    username = args.username
    password_hash = pwd_context.hash(password)
    is_enabled = not args.disabled
    is_superuser = args.superuser

    # Create user in PostgreSQL
    with psycopg.connect(connection_string) as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO user_ (id, username, password_hash, is_enabled, is_superuser)
                        VALUES(%s, %s, %s, %s, %s)
            """,
            [id_, username, password_hash, is_enabled, is_superuser],
        )

    # Echo successful creation
    print(f"""User successfully created!
id: {id}
username: {username}
is_enabled: {is_enabled}
is_superuser: {is_superuser}""")


if __name__ == "__main__":
    main()
