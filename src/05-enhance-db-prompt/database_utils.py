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
import logging # ADDED: Import logging

logger = logging.getLogger(__name__) # ADDED: Get a logger instance for this module

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


def get_engine(): # CHANGED: Removed verbose=False argument
    """Initializes and returns a SQLAlchemy engine."""
    global _engine
    if _engine is None:
        if not all([DB_USER, DB_PASSWORD, DB_DSN]):
            logger.error("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.") # CHANGED: print to logger.error
            raise ValueError("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
        try:
            # Use the DB_DSN string directly as confirmed working
            database_url = f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_DSN}"
            _engine = create_engine(database_url)
            # Test connection
            with _engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
            logger.info("SQLAlchemy Engine created and connection tested successfully.") # CHANGED: print to logger.info
        except exc.SQLAlchemyError as e:
            _engine = None # Reset engine on failure
            logger.exception(f"Failed to create SQLAlchemy engine or connect: {e}") # CHANGED: print to logger.exception
            raise ConnectionError(f"Failed to create SQLAlchemy engine or connect: {e}")
    return _engine

def get_table_reflection(table_name: str) -> Table: # CHANGED: Removed verbose=False argument
    """
    Reflects a table from the database and returns its SQLAlchemy Table object.
    It uses the specified schema owner and the exact casing of the table_name.
    """
    engine = get_engine() # No verbose argument passed here
    try:
        # Debugging: Print values before reflection
        logger.debug(f"Reflecting table '{table_name}' from schema '{TABLE_OWNER_SCHEMA}'") # CHANGED: print to logger.debug

        # The 'schema' argument is crucial here to look for the table in the correct owner's schema
        # Use the exact table_name as it's now expected to have correct casing (e.g., 'electricvehicles')
        # Removed .upper() to ensure exact casing is used for reflection
        table = Table(table_name, _metadata, autoload_with=engine, schema=TABLE_OWNER_SCHEMA)
        return table
    except exc.NoSuchTableError:
        logger.error(f"Table '{table_name}' not found in schema '{TABLE_OWNER_SCHEMA}'.") # CHANGED: raise to logger.error
        raise ValueError(f"Table '{table_name}' not found in schema '{TABLE_OWNER_SCHEMA}'. "
                         "Please check table name casing and schema owner.")
    except exc.SQLAlchemyError as e:
        logger.exception(f"Error reflecting table '{table_name}': {e}") # CHANGED: raise to logger.exception
        raise RuntimeError(f"Error reflecting table '{table_name}': {e}")

def get_table_schema_string(table_name: str) -> str: # CHANGED: Removed verbose=False argument
    """Retrieves the schema (column names and types) of a table as a string."""
    try:
        table = get_table_reflection(table_name) # No verbose argument passed here
        schema_info = f"Table: {TABLE_OWNER_SCHEMA}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"
        return schema_info
    except (ValueError, RuntimeError) as e:
        logger.warning(f"Failed to get table schema for '{table_name}': {e}") # CHANGED: return str(e) to logger.warning
        return str(e)

def execute_read_query(table_name: str, conditions: str = None, limit: int = 5) -> str: # CHANGED: Removed verbose=False argument
    """
    Executes a read query on the specified table with optional conditions and limit.
    Returns results as a formatted string.
    """
    engine = get_engine() # No verbose argument passed here
    connection: Connection = None
    try:
        # Reflect the table first to get its structure (important for column names)
        # Pass the table_name as is, assuming it now has the correct casing (e.g., 'electricvehicles')
        table = get_table_reflection(table_name) # No verbose argument passed here
        connection = engine.connect()

        # Build the SELECT statement dynamically
        select_cols = [c.name for c in table.columns]
        # IMPORTANT: Use the full qualified table name for queries (e.g., RW_USER.electricvehicles)
        # Ensure the table.name is used here, which comes from reflection and has correct casing
        #full_qualified_table_name = f'"{TABLE_OWNER_SCHEMA}"."{table.name}"' # Quote owner and name for case sensitivity
        full_qualified_table_name = f'{table.name}'

        stmt_template = f"SELECT {', '.join(select_cols)} FROM {full_qualified_table_name}"

        # Add WHERE clause if conditions are provided
        if conditions:
            stmt_template += f" WHERE {conditions}"

        # Add LIMIT/ROWNUM for Oracle
        if limit is not None:
            if "WHERE" in stmt_template:
                 stmt = text(f"{stmt_template} AND ROWNUM <= {limit}")
            else:
                 stmt = text(f"{stmt_template} WHERE ROWNUM <= {limit}")
        else:
            stmt = text(stmt_template) # If no limit, use the basic template

        logger.debug(f"Executing SQL query: {stmt.compile(engine)}") # CHANGED: print to logger.debug

        result = connection.execute(stmt)
        rows = result.fetchall()

        if not rows:
            logger.info(f"No data found in '{table_name}' for the given conditions.") # CHANGED: return string to logger.info
            return f"No data found in '{table_name}' for the given conditions." # Still return string for expected output

        # Format output
        column_names = result.keys()
        formatted_results = [", ".join(column_names)] # Header row
        for row in rows:
            # Corrected line: Removed extraneous non-English characters
            formatted_results.append(", ".join(map(str, row)))

        return "\n".join(formatted_results)

    except (ValueError, RuntimeError, exc.SQLAlchemyError) as e:
        logger.exception(f"Error executing query: {e}") # CHANGED: return string to logger.exception
        return f"Error executing query: {e}" # Still return string for expected output
    finally:
        if connection:
            connection.close()
            logger.debug("Database connection closed.") # ADDED: Debug log for closing connection

if __name__ == '__main__':
    # ADDED: Basic logging configuration for when database_utils.py is run directly
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running database_utils.py directly for testing.") # ADDED: Info log for direct run

    # Simple tests for database_utils
    try:
        # Use the exact casing that was discovered from inspection
        test_table_name = "electricvehicles"

        logger.info(f"--- Testing get_table_schema_string for {test_table_name} ---") # CHANGED: print to logger.info
        schema = get_table_schema_string(test_table_name)
        print(schema) # Keep print for displaying the actual schema output to user

        logger.info(f"\n--- Testing execute_read_query for {test_table_name} (first 3 rows) ---") # CHANGED: print to logger.info
        data = execute_read_query(test_table_name, limit=3)
        print(data) # Keep print for displaying the actual data output to user

        logger.info(f"\n--- Testing execute_read_query with a condition for {test_table_name} ---") # CHANGED: print to logger.info
        data_filtered = execute_read_query(test_table_name, conditions="MODEL LIKE 'Tesla%'", limit=2)
        print(data_filtered) # Keep print for displaying the actual data output to user

        logger.info("\n--- Testing non-existent table ---") # CHANGED: print to logger.info
        non_existent_schema = get_table_schema_string("NonExistentTable")
        print(non_existent_schema) # Keep print for displaying the error string

    except Exception as e:
        logger.critical(f"Overall test error in database_utils: {e}", exc_info=True) # CHANGED: print to logger.critical with traceback

