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
            raise ValueError("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
        try:
            # Use the DB_DSN string directly as confirmed working
            database_url = f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_DSN}"
            _engine = create_engine(database_url)
            # Test connection
            with _engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
            print("SQLAlchemy Engine created and connection tested successfully.")
        except exc.SQLAlchemyError as e:
            _engine = None # Reset engine on failure
            raise ConnectionError(f"Failed to create SQLAlchemy engine or connect: {e}")
    return _engine

def get_table_reflection(table_name: str) -> Table:
    """
    Reflects a table from the database and returns its SQLAlchemy Table object.
    It uses the specified schema owner and the exact casing of the table_name.
    """
    engine = get_engine()
    try:
        # Debugging: Print values before reflection
        print(f"Debug: Reflecting table '{table_name}' from schema '{TABLE_OWNER_SCHEMA}'")

        # The 'schema' argument is crucial here to look for the table in the correct owner's schema
        # Use the exact table_name as it's now expected to have correct casing (e.g., 'electricvehicles')
        # Removed .upper() to ensure exact casing is used for reflection
        table = Table(table_name, _metadata, autoload_with=engine, schema=TABLE_OWNER_SCHEMA)
        return table
    except exc.NoSuchTableError:
        raise ValueError(f"Table '{table_name}' not found in schema '{TABLE_OWNER_SCHEMA}'. "
                         "Please check table name casing and schema owner.")
    except exc.SQLAlchemyError as e:
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
        return str(e)

def execute_read_query(table_name: str, conditions: str = None, limit: int = 5) -> str:
    """
    Executes a read query on the specified table with optional conditions and limit.
    Returns results as a formatted string.
    """
    engine = get_engine()
    connection: Connection = None
    try:
        # Reflect the table first to get its structure (important for column names)
        # Pass the table_name as is, assuming it now has the correct casing (e.g., 'electricvehicles')
        table = get_table_reflection(table_name)
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

        print(f"Executing SQL query: {stmt.compile(engine)}") # For debugging

        result = connection.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return f"No data found in '{table_name}' for the given conditions."

        # Format output
        column_names = result.keys()
        formatted_results = [", ".join(column_names)] # Header row
        for row in rows:
            # Corrected line: Removed extraneous non-English characters
            formatted_results.append(", ".join(map(str, row)))

        return "\n".join(formatted_results)

    except (ValueError, RuntimeError, exc.SQLAlchemyError) as e:
        return f"Error executing query: {e}"
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    # Simple tests for database_utils
    try:
        # Use the exact casing that was discovered from inspection
        test_table_name = "electricvehicles"

        print(f"--- Testing get_table_schema_string for {test_table_name} ---")
        schema = get_table_schema_string(test_table_name)
        print(schema)

        print(f"\n--- Testing execute_read_query for {test_table_name} (first 3 rows) ---")
        data = execute_read_query(test_table_name, limit=3)
        print(data)

        print(f"\n--- Testing execute_read_query with a condition for {test_table_name} ---")
        data_filtered = execute_read_query(test_table_name, conditions="MODEL LIKE 'Tesla%'", limit=2)
        print(data_filtered)

        print("\n--- Testing non-existent table ---")
        non_existent_schema = get_table_schema_string("NonExistentTable")
        print(non_existent_schema)

    except Exception as e:
        print(f"Overall test error: {e}")

