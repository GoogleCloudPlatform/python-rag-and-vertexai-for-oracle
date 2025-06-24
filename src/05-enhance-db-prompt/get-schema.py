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
from sqlalchemy import create_engine, MetaData, Table, exc, text, inspect # Added 'inspect'
from sqlalchemy.engine import Connection

# Load environment variables from .env file at the top level
load_dotenv()

def get_oracle_table_schema(table_name: str, schema_owner: str) -> str:
    """
    Connects to an Oracle database and reflects the schema of a specified table.
    Returns a formatted string of column names and their types.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    # Retrieve the full DSN string directly from .env
    db_dsn_string = os.getenv("DB_DSN")

    if not all([db_user, db_password, db_dsn_string]):
        return "Error: Missing DB connection details in .env (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)."

    # Construct the full database URL for SQLAlchemy
    # Use the DB_DSN string directly as confirmed working
    database_url = f"oracle+oracledb://{db_user}:{db_password}@{db_dsn_string}"

    engine = None
    connection: Connection = None
    try:
        # 1. Create SQLAlchemy Engine
        engine = create_engine(database_url)

        # Test connection (optional, but good for early error detection)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        print("Successfully connected to the Oracle database.")

        # --- DEEPER DEBUGGING STEP: Use Inspector ---
        inspector = inspect(engine)
        # Get a list of all table names visible in the specified schema
        # This is a direct query to the data dictionary to list tables
        visible_tables = inspector.get_table_names(schema=schema_owner)
        print(f"Debug: Tables visible in schema '{schema_owner}': {visible_tables}")

        # Check if the target table (with its exact casing) is in the visible list
        if table_name not in visible_tables: # Check against the exact casing
            return (f"Error: Table '{table_name}' was not found in the list of tables "
                    f"visible in schema '{schema_owner}' through SQLAlchemy's inspector. "
                    f"Visible tables: {visible_tables}. Please ensure casing matches database." )
        # --- END DEEPER DEBUGGING STEP ---


        # 2. Reflect the table metadata
        metadata = MetaData()
        # Debugging: Print values before reflection
        print(f"Debug: Attempting to reflect table '{table_name}' with schema '{schema_owner}'")

        # The 'schema' argument is crucial here to look for the table in the correct owner's schema
        # Use the exact table_name as it's now expected to have correct casing
        table = Table(table_name, metadata, autoload_with=engine, schema=schema_owner)

        # 3. Format the schema information
        schema_info = f"Table: {schema_owner}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"

        return schema_info

    except exc.NoSuchTableError:
        # The specific error message if Table() still fails
        return f"Error: Table '{table_name}' not found in schema '{schema_owner}' via direct reflection. This might indicate permission issues or exact naming discrepancies."
    except exc.OperationalError as e:
        return f"Error connecting to the database or invalid credentials: {e}"
    except exc.SQLAlchemyError as e:
        return f"An SQLAlchemy error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        # Ensure the engine and connection are properly disposed
        if engine:
            engine.dispose()
        print("Database connection closed.")


if __name__ == "__main__":
    # Set the target_table to the exact casing found in the database
    target_table = "electricvehicles" # <--- CHANGED TO LOWERCASE

    owner_schema = os.getenv("DB_TABLE_OWNER_SCHEMA")

    if not owner_schema:
        print("Error: DB_TABLE_OWNER_SCHEMA not set in .env file.")
    else:
        schema_output = get_oracle_table_schema(target_table, owner_schema)
        print("\n--- Table Schema ---")
        print(schema_output)

