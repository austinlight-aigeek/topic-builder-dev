import argparse
import sys
import os
import glob
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import psycopg
from sqlalchemy import URL

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
connection_string = URL.create(
    "postgresql",
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    int(POSTGRES_PORT),
    POSTGRES_DB,
).render_as_string(hide_password=False)

DUMP_PATH = os.getenv("DUMP_PATH", "src/db/")


def find_latest_sql_dump(
    path: str, starts_with: str = "sentence_", ends_with: str = ".sql"
) -> str:
    pattern = os.path.join(path, f"{starts_with}*{ends_with}")
    files = glob.glob(pattern)

    if files:
        # Return the latest file based on modification time
        return max(files, key=os.path.getmtime)
    else:
        return None


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        "load_sentence_sample.py",
        description="Populate sentence table in the NLP Topic Builder application",
    )

    # Load latest SQL dump file
    sql = find_latest_sql_dump(path=DUMP_PATH)

    if sql:
        with psycopg.connect(connection_string) as conn, conn.cursor() as cur:
            # Read the contents of the latest SQL file
            with open(sql, "r", encoding="utf-8") as file:
                sql_commands = file.read()

            cur.execute(sql_commands)
            conn.commit()
            print(f"Executed the SQL file: {sql}")

    else:
        print(f"Nothing to execute")


if __name__ == "__main__":
    main()
