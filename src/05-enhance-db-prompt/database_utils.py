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

# Load values from .env file
load_dotenv()

# Get connection details from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# Construct the Oracle connection string for SQLAlchemy
# Example: oracle+oracledb://user:password@host:port/service_name
# Ensure you have the 'oracledb' driver installed for SQLAlchemy
DATABASE_URL = f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_DSN}"

_engine = None # Global engine to reuse connection pool
_metadata = MetaData() # Global metadata object


# Add this global variable or get it from .env for the schema owner
# IMPORTANT: This should be the actual username that owns the table in Oracle,
TABLE_OWNER_SCHEMA = os.getenv("DB_TABLE_OWNER_SCHEMA") # Add this line or similar


def get_engine():
    """Initializes and returns a SQLAlchemy engine."""
    global _engine
    if _engine is None:
        if not all([DB_USER, DB_PASSWORD, DB_DSN]):
            raise ValueError("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
        try:
            _engine = create_engine(DATABASE_URL)
            # Test connection
            with _engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
            print("SQLAlchemy Engine created and connection tested successfully.")
        except exc.SQLAlchemyError as e:
            _engine = None # Reset engine on failure
            raise ConnectionError(f"Failed to create SQLAlchemy engine or connect: {e}")
    return _engine

def get_table_reflection(table_name: str) -> Table:
    """Reflects a table from the database and returns its SQLAlchemy Table object."""
    engine = get_engine()
    try:
        table = Table(table_name.upper(), _metadata, autoload_with=engine, schema=TABLE_OWNER_SCHEMA)
        return table
    except exc.NoSuchTableError:
        raise ValueError(f"Table '{table_name}' does not exist in the database.")
    except exc.SQLAlchemyError as e:
        raise RuntimeError(f"Error reflecting table '{table_name}': {e}")

def get_table_schema_string(table_name: str) -> str:
    """Retrieves the schema (column names and types) of a table as a string."""
    try:
        table = get_table_reflection(table_name)
        schema_info = f"Table: {table.name}\nColumns:\n"
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
        table_name = table_name.upper() # Ensure the table name is uppercase for Oracle
        table = get_table_reflection(table_name)
        connection = engine.connect()

        # Build the SELECT statement dynamically
        select_cols = [c.name for c in table.columns]
        stmt = text(f"SELECT {', '.join(select_cols)} FROM {table_name}")

        # Add WHERE clause if conditions are provided
        if conditions:
            stmt = text(f"SELECT {', '.join(select_cols)} FROM {table_name} WHERE {conditions}")

        # Add LIMIT/ROWNUM for Oracle
        if limit is not None:
            if conditions:
                 stmt = text(f"SELECT {', '.join(select_cols)} FROM {table_name} WHERE {conditions} AND ROWNUM <= {limit}")
            else:
                 stmt = text(f"SELECT {', '.join(select_cols)} FROM {table_name} WHERE ROWNUM <= {limit}")

        print(f"Executing SQL query: {stmt.compile(engine)}") # For debugging

        result = connection.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return f"No data found in '{table_name}' for the given conditions."

        # Format output
        column_names = result.keys()
        formatted_results = [", ".join(column_names)] # Header row
        for row in rows:
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
        print("--- Testing get_table_schema_string for ElectricVehicles ---")
        schema = get_table_schema_string("ElectricVehicles")
        print(schema)

        print("\n--- Testing execute_read_query for ElectricVehicles (first 3 rows) ---")
        data = execute_read_query("ElectricVehicles", limit=3)
        print(data)

        print("\n--- Testing execute_read_query with a condition ---")
        data_filtered = execute_read_query("ElectricVehicles", conditions="MODEL LIKE 'Tesla%'", limit=2)
        print(data_filtered)

        print("\n--- Testing non-existent table ---")
        non_existent_schema = get_table_schema_string("NonExistentTable")
        print(non_existent_schema)

    except Exception as e:
        print(f"Overall test error: {e}")
