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
import logging # ADDED: Import logging

logger = logging.getLogger(__name__) # ADDED: Get a logger instance for this module

# Load environment variables from .env file at the top level
load_dotenv()

def get_oracle_table_schema(table_name: str, schema_owner: str) -> str: # CHANGED: Removed verbose argument
    """
    Connects to an Oracle database and reflects the schema of a specified table.
    Returns a formatted string of column names and their types.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    #db_dsn_string = os.getenv("DB_DSN")
    db_dsn_string = os.getenv("SQLALCHEMY_URL")

    if not all([db_user, db_password, db_dsn_string]):
        logger.error("Error: Missing DB connection details in .env (DB_USER, DB_PASSWORD, DB_DSN).") # CHANGED: return string to logger.error
        return "Error: Missing DB connection details in .env (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)." # Still return string for expected output

    database_url = f"oracle+oracledb://{db_user}:{db_password}@{db_dsn_string}"

    engine = None
    connection: Connection = None
    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        logger.info("Successfully connected to the Oracle database.") # CHANGED: print to logger.info

        inspector = inspect(engine)
        visible_tables = inspector.get_table_names(schema=schema_owner)
        logger.debug(f"Debug: Tables visible in schema '{schema_owner}': {visible_tables}") # CHANGED: print to logger.debug

        if table_name not in visible_tables:
            logger.error(f"Table '{table_name}' was not found in schema '{schema_owner}'. Visible tables: {visible_tables}.") # CHANGED: return string to logger.error
            return (f"Error: Table '{table_name}' was not found in the list of tables "
                    f"visible in schema '{schema_owner}' through SQLAlchemy's inspector. "
                    f"Visible tables: {visible_tables}. Please ensure casing matches database." ) # Still return string for expected output

        metadata = MetaData()
        logger.debug(f"Debug: Attempting to reflect table '{table_name}' with schema '{schema_owner}'") # CHANGED: print to logger.debug

        table = Table(table_name, metadata, autoload_with=engine, schema=schema_owner)

        schema_info = f"Table: {schema_owner}.{table.name}\nColumns:\n"
        for column in table.columns:
            schema_info += f"- {column.name}: {column.type}\n"

        return schema_info

    except exc.NoSuchTableError:
        logger.error(f"Error: Table '{table_name}' not found in schema '{schema_owner}' via direct reflection.") # CHANGED: return string to logger.error
        return f"Error: Table '{table_name}' not found in schema '{schema_owner}' via direct reflection. This might indicate permission issues or exact naming discrepancies." # Still return string for expected output
    except exc.OperationalError as e:
        logger.exception(f"Error connecting to the database or invalid credentials: {e}") # CHANGED: return string to logger.exception
        return f"Error connecting to the database or invalid credentials: {e}" # Still return string for expected output
    except exc.SQLAlchemyError as e:
        logger.exception(f"An SQLAlchemy error occurred: {e}") # CHANGED: return string to logger.exception
        return f"An SQLAlchemy error occurred: {e}" # Still return string for expected output
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}") # CHANGED: return string to logger.exception
        return f"An unexpected error occurred: {e}" # Still return string for expected output
    finally:
        if engine:
            engine.dispose()
        logger.debug("Database connection closed.") # CHANGED: print to logger.debug


if __name__ == "__main__":
    # ADDED: Basic logging configuration for when get-schema.py is run directly
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running get-schema.py directly for testing.") # ADDED: Info log for direct run

    target_table = "electricvehicles"
    owner_schema = os.getenv("DB_TABLE_OWNER_SCHEMA")

    if not owner_schema:
        logger.error("DB_TABLE_OWNER_SCHEMA not set in .env file.") # CHANGED: print to logger.error
        print("Error: DB_TABLE_OWNER_SCHEMA not set in .env file.") # Keep print for final user output
    else:
        logger.info("\n--- Table Schema ---") # CHANGED: print to logger.info
        schema_output = get_oracle_table_schema(target_table, owner_schema)
        print(schema_output) # Keep print for displaying the actual schema output to user
