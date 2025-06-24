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
import json # ADDED: Import json module

logger = logging.getLogger(__name__)

# Load values from .env file at the very top to ensure variables are available
load_dotenv()

# Get connection details from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# This will be the schema where the tables that DB_USER (ro_user) needs to access reside
DB_TABLE_OWNER_SCHEMA = os.getenv("DB_TABLE_OWNER_SCHEMA")


_engine = None # Global engine to reuse connection pool
_metadata = MetaData() # Global metadata object

# REMOVED: Hardcoded TABLE_METADATA dictionary

# ADDED: Load TABLE_METADATA from a JSON file
_table_metadata_cache = None # Cache to load once

def _load_table_metadata():
    global _table_metadata_cache
    if _table_metadata_cache is None:
        metadata_file_path = os.path.join(os.path.dirname(__file__), 'table_metadata.json')
        try:
            with open(metadata_file_path, 'r') as f:
                # Store keys as uppercase for robust lookup against DB names
                raw_metadata = json.load(f)
                _table_metadata_cache = {k.upper(): v for k, v in raw_metadata.items()}
            logger.info(f"Loaded table metadata from {metadata_file_path}")
        except FileNotFoundError:
            logger.error(f"Table metadata file not found at: {metadata_file_path}. Using empty metadata.")
            _table_metadata_cache = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {metadata_file_path}: {e}. Using empty metadata.")
            _table_metadata_cache = {}
    return _table_metadata_cache


def get_engine():
    """Initializes and returns a SQLAlchemy engine using DB_USER credentials."""
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
            logger.info("SQLAlchemy Engine created and connection tested successfully using DB_USER.")
        except exc.SQLAlchemyError as e:
            _engine = None
            logger.exception(f"Failed to create SQLAlchemy engine or connect: {e}")
            raise ConnectionError(f"Failed to create SQLAlchemy engine or connect: {e}")
    return _engine

def get_table_reflection(table_name: str) -> Table:
    """
    Reflects a table from the database and returns its SQLAlchemy Table object.
    It uses the schema specified by DB_TABLE_OWNER_SCHEMA and the exact casing of the table_name.
    """
    engine = get_engine()
    try:
        logger.debug(f"Reflecting table '{table_name}' from schema '{DB_TABLE_OWNER_SCHEMA}'")

        table = Table(table_name, _metadata, autoload_with=engine, schema=DB_TABLE_OWNER_SCHEMA)
        return table
    except exc.NoSuchTableError:
        logger.error(f"Table '{table_name}' not found in schema '{DB_TABLE_OWNER_SCHEMA}'.")
        raise ValueError(f"Table '{table_name}' not found in schema '{DB_TABLE_OWNER_SCHEMA}'. "
                         "Please check table name casing and schema owner.")
    except exc.SQLAlchemyError as e:
        logger.exception(f"Error reflecting table '{table_name}': {e}")
        raise RuntimeError(f"Error reflecting table '{table_name}': {e}")

def get_table_schema_string(table_name: str) -> str:
    """Retrieves the schema (column names and types) of a table as a string."""
    try:
        table = get_table_reflection(table_name)
        schema_info = f"Table: {DB_TABLE_OWNER_SCHEMA}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"
        return schema_info
    except (ValueError, RuntimeError) as e:
        logger.warning(f"Failed to get table schema for '{table_name}': {e}")
        return str(e)

def get_all_accessible_tables(schema_name: str = None) -> list[dict]:
    """
    Connects to the Oracle database and returns a list of dictionaries,
    each containing table name and its description.
    Filters by _load_table_metadata() and actual accessible tables.
    """
    engine = get_engine()
    accessible_tables_from_db = []
    metadata = _load_table_metadata() # Load metadata

    try:
        inspector = inspect(engine)
        db_tables = inspector.get_table_names(schema=schema_name or DB_TABLE_OWNER_SCHEMA)
        logger.debug(f"Tables found in database: {db_tables}")

        for table_name_db in db_tables: # Iterate through actual DB tables
            # Find description using uppercase for robust matching
            description = metadata.get(table_name_db.upper(), "No specific description available.")
            accessible_tables_from_db.append({
                "name": table_name_db, # Use the original casing from DB
                "description": description
            })
        logger.debug(f"Filtered and described accessible tables: {accessible_tables_from_db}")
        return accessible_tables_from_db
    except exc.SQLAlchemyError as e:
        logger.exception(f"Error getting all accessible tables: {e}")
        return []
    finally:
        if engine:
            engine.dispose()
            logger.debug("Database engine disposed after table listing.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running database_utils.py directly for testing.")

    try:
        test_table_name = "ELECTRICVEHICLES"

        logger.info(f"--- Testing get_table_schema_string for {test_table_name} ---")
        schema = get_table_schema_string(test_table_name)
        print(schema)

        logger.info("\n--- Testing non-existent table ---")
        non_existent_schema = get_table_schema_string("NonExistentTable")
        print(non_existent_schema)

        logger.info(f"\n--- Testing get_all_accessible_tables in schema '{DB_TABLE_OWNER_SCHEMA}' ---")
        all_tables_with_desc = get_all_accessible_tables(DB_TABLE_OWNER_SCHEMA)
        if all_tables_with_desc:
            print("Accessible Tables (with descriptions):")
            for table_info in all_tables_with_desc:
                print(f"- {table_info['name']}: {table_info['description']}")
        else:
            print("No accessible tables found or an error occurred.")
            logger.warning(f"No tables returned by get_all_accessible_tables for schema '{DB_TABLE_OWNER_SCHEMA}'. Check permissions/schema.")

    except Exception as e:
        logger.critical(f"Overall test error in database_utils: {e}", exc_info=True)
