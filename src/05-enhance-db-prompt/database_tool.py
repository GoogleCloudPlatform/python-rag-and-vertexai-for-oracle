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
from langchain.tools import tool
import logging

# Import the new database utilities
# MODIFIED: Added get_engine import for the new count_electric_vehicles tool
from database_utils import get_table_schema_string, execute_read_query, get_engine
from sqlalchemy import text # ADDED: Import text for raw SQL queries

logger = logging.getLogger(__name__)

@tool
def get_table_schema(table_name: str) -> str:
    """
    Retrieves the schema (column names and data types) for a given database table.
    Use this tool BEFORE querying data from a table if you are unsure about its structure
    or the available columns for filtering.
    Input should be the exact table name, e.g., 'electricvehicles' (lowercase if created with quotes).
    """
    logger.debug(f"Tool Call: get_table_schema for table: '{table_name}'")
    return get_table_schema_string(table_name)

@tool
def query_electric_vehicles(conditions: str = None, limit: int = 5) -> str:
    """
    Queries the electricvehicles table in the Oracle Database.
    Use this tool to get specific data about electric vehicles.
    'conditions' is an optional SQL WHERE clause (e.g., "MODEL = 'Tesla Model 3' AND CITY = 'Seattle'").
    'limit' is an optional integer to limit the number of rows returned (defaults to 5).
    Ensure you know the table schema before constructing complex conditions.
    The table name is 'electricvehicles' (lowercase).
    """
    table_name = "electricvehicles"

    logger.debug(f"Tool Call: query_electric_vehicles with conditions: '{conditions}', limit: {limit}")
    logger.debug(f"Debug: query_electric_vehicles is using table_name: '{table_name}'")
    return execute_read_query(table_name, conditions, limit)

@tool
def count_electric_vehicles() -> str:
    """
    Returns the total number of records in the electricvehicles table.
    Use this tool to get a count of all electric vehicles without retrieving actual data.
    """
    logger.debug("Tool Call: count_electric_vehicles")
    engine = get_engine() # Get the SQLAlchemy engine
    connection = None
    try:
        connection = engine.connect()
        # Explicitly query the count for the 'electricvehicles' table
        # Assuming 'electricvehicles' is the correct unquoted, lowercase table name in Oracle
        result = connection.execute(text(f"SELECT COUNT(*) FROM electricvehicles"))
        count = result.scalar() # Get the single scalar result (the count)
        logger.info(f"Total count for electricvehicles: {count}")
        return f"The total number of electric vehicle records is: {count}"
    except Exception as e:
        logger.exception(f"Error counting records in electricvehicles: {e}")
        return f"Error getting count: {e}"
    finally:
        if connection:
            connection.close()
