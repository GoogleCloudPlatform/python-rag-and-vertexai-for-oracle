# database_utils.py
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
import oracledb
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, exc
from sqlalchemy.engine import Connection
from sqlalchemy.schema import Table, MetaData, Column
import logging

logger = logging.getLogger(__name__)

# Load values from .env file at the very top to ensure variables are available
load_dotenv()

# Get connection details from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# IMPORTANT: This should be the actual username that owns the table in Oracle,
# as determined by the `inspector.get_table_names(schema=...)` debug output
TABLE_OWNER_SCHEMA = os.getenv("DB_TABLE_OWNER_SCHEMA")


_engine = None # Global engine to reuse connection pool
_metadata = MetaData() # Global metadata object


def get_engine():
    """Initializes and returns a SQLAlchemy engine."""
    global _engine
    if _engine is None:
        if not all([DB_USER, DB_PASSWORD, DB_DSN]):
            logger.error("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
            raise ValueError("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
        try:
            database_url = f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_DSN}"
            _engine = create_engine(database_url)
            # Test connection
            with _engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
            logger.info("SQLAlchemy Engine created and connection tested successfully.")
        except exc.SQLAlchemyError as e:
            _engine = None # Reset engine on failure
            logger.exception(f"Failed to create SQLAlchemy engine or connect: {e}")
            raise ConnectionError(f"Failed to create SQLAlchemy engine or connect: {e}")
    return _engine

def get_table_reflection(table_name: str) -> Table:
    """
    Reflects a table from the database and returns its SQLAlchemy Table object.
    It uses the specified schema owner and the exact casing of the table_name.
    """
    engine = get_engine()
    try:
        logger.debug(f"Reflecting table '{table_name}' from schema '{TABLE_OWNER_SCHEMA}'")

        table = Table(table_name, _metadata, autoload_with=engine, schema=TABLE_OWNER_SCHEMA)
        return table
    except exc.NoSuchTableError:
        logger.error(f"Table '{table_name}' not found in schema '{TABLE_OWNER_SCHEMA}'.")
        raise ValueError(f"Table '{table_name}' not found in schema '{TABLE_OWNER_SCHEMA}'. "
                         "Please check table name casing and schema owner.")
    except exc.SQLAlchemyError as e:
        logger.exception(f"Error reflecting table '{table_name}': {e}")
        raise RuntimeError(f"Error reflecting table '{table_name}': {e}")

def get_table_schema_string(table_name: str) -> str:
    """Retrieves the schema (column names and types) of a table as a string."""
    try:
        table = get_table_reflection(table_name)
        schema_info = f"Table: {TABLE_OWNER_SCHEMA}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"
        return schema_info
    except (ValueError, RuntimeError) as e:
        logger.warning(f"Failed to get table schema for '{table_name}': {e}")
        return str(e)

# REMOVED: execute_read_query function, as its functionality is now absorbed by query_database

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running database_utils.py directly for testing.")

    try:
        test_table_name = "electricvehicles"

        logger.info(f"--- Testing get_table_schema_string for {test_table_name} ---")
        schema = get_table_schema_string(test_table_name)
        print(schema)

        logger.info("\n--- Testing non-existent table ---")
        non_existent_schema = get_table_schema_string("NonExistentTable")
        print(non_existent_schema)

        # Note: Direct testing of query_database or aggregate queries
        # would need to be added here if you want to test database_utils
        # in isolation after removing execute_read_query.
        # This block primarily tests schema retrieval now.

    except Exception as e:
        logger.critical(f"Overall test error in database_utils: {e}", exc_info=True)
