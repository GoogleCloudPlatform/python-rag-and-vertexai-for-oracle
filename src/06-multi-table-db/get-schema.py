# get-schema.py
"""
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, exc, text, inspect
from sqlalchemy.engine import Connection
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file at the top level
load_dotenv()

# NEW: Import get_all_accessible_tables from database_utils
from database_utils import get_all_accessible_tables, DB_TABLE_OWNER_SCHEMA # Also import DB_TABLE_OWNER_SCHEMA

def get_oracle_table_schema(table_name: str, schema_owner: str) -> str:
    """
    Connects to an Oracle database and reflects the schema of a specified table.
    Returns a formatted string of column names and their types.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_dsn_string = os.getenv("DB_DSN")

    if not all([db_user, db_password, db_dsn_string]):
        logger.error("Error: Missing DB connection details in .env (DB_USER, DB_PASSWORD, DB_DSN).")
        return "Error: Missing DB connection details in .env (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)."

    database_url = f"oracle+oracledb://{db_user}:{db_password}@{db_dsn_string}"

    engine = None
    connection: Connection = None
    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        logger.info("Successfully connected to the Oracle database.")

        inspector = inspect(engine)
        visible_tables = inspector.get_table_names(schema=schema_owner)
        logger.debug(f"Debug: Tables visible in schema '{schema_owner}': {visible_tables}")

        if table_name not in visible_tables:
            logger.error(f"Table '{table_name}' was not found in schema '{schema_owner}'. Visible tables: {visible_tables}.")
            return (f"Error: Table '{table_name}' was not found in the list of tables "
                    f"visible in schema '{schema_owner}' through SQLAlchemy's inspector. "
                    f"Visible tables: {visible_tables}. Please ensure casing matches database." )

        metadata = MetaData()
        logger.debug(f"Debug: Attempting to reflect table '{table_name}' with schema '{schema_owner}'")

        table = Table(table_name, metadata, autoload_with=engine, schema=schema_owner)

        schema_info = f"Table: {schema_owner}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"

        return schema_info

    except exc.NoSuchTableError:
        logger.error(f"Error: Table '{table_name}' not found in schema '{schema_owner}' via direct reflection.")
        return f"Error: Table '{table_name}' not found in schema '{schema_owner}' via direct reflection. This might indicate permission issues or exact naming discrepancies."
    except exc.OperationalError as e:
        logger.exception(f"Error connecting to the database or invalid credentials: {e}")
        return f"Error connecting to the database or invalid credentials: {e}"
    except exc.SQLAlchemyError as e:
        logger.exception(f"An SQLAlchemy error occurred: {e}")
        return f"An SQLAlchemy error occurred: {e}"
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"
    finally:
        if engine:
            engine.dispose()
        logger.debug("Database connection closed.")


if __name__ == "__main__":
    # Configure logging for direct run of this script
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running get-schema.py directly for testing.")

    # --- Existing Test for single table schema ---
    target_table = "electricvehicles" # Example table, ensure ro_user can select from it
    owner_schema = os.getenv("DB_TABLE_OWNER_SCHEMA") # Use the schema from .env

    if not owner_schema:
        logger.error("DB_TABLE_OWNER_SCHEMA not set in .env file.")
        print("Error: DB_TABLE_OWNER_SCHEMA not set in .env file.")
    else:
        logger.info(f"\n--- Testing schema for table: {target_table} in schema: {owner_schema} ---")
        schema_output = get_oracle_table_schema(target_table, owner_schema)
        print(schema_output)

    # --- NEW POC Test for listing all accessible tables ---
    logger.info(f"\n--- POC: Listing all accessible tables in schema: {DB_TABLE_OWNER_SCHEMA} ---")
    if DB_TABLE_OWNER_SCHEMA:
        all_tables = get_all_accessible_tables(DB_TABLE_OWNER_SCHEMA) # Call the new function
        if all_tables:
            print(f"Tables accessible to DB_USER ('{os.getenv('DB_USER')}') in schema '{DB_TABLE_OWNER_SCHEMA}':")
            for table in all_tables:
                print(f"- {table}")
        else:
            print(f"No accessible tables found in schema '{DB_TABLE_OWNER_SCHEMA}' or an error occurred.")
            logger.warning(f"No tables returned by get_all_accessible_tables for schema '{DB_TABLE_OWNER_SCHEMA}'. Check permissions/schema.")
    else:
        print("Cannot list all tables: DB_TABLE_OWNER_SCHEMA is not set in .env.")
        logger.error("Cannot list all tables: DB_TABLE_OWNER_SCHEMA is not set in .env.")
