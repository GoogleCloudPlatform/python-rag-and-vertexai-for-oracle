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
import logging # ADDED: Import logging

# Import the new database utilities
from database_utils import get_table_schema_string, execute_read_query

logger = logging.getLogger(__name__) # ADDED: Get a logger instance for this module

@tool
def get_table_schema(table_name: str) -> str:
    """
    Retrieves the schema (column names and data types) for a given database table.
    Use this tool BEFORE querying data from a table if you are unsure about its structure
    or the available columns for filtering.
    Input should be the exact table name, e.g., 'electricvehicles' (lowercase if created with quotes).
    """
    logger.debug(f"Tool Call: get_table_schema for table: '{table_name}'") # CHANGED: print to logger.debug
    # Pass the table_name as is, assuming the user/LLM provides correct casing
    return get_table_schema_string(table_name) # No 'verbose' arg needed here now

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
    # Set the table name to the exact casing discovered during inspection
    # This ensures consistency with how the table is stored in Oracle
    table_name = "electricvehicles" # Use the confirmed lowercase name

    logger.debug(f"Tool Call: query_electric_vehicles with conditions: '{conditions}', limit: {limit}") # CHANGED: print to logger.debug
    logger.debug(f"Debug: query_electric_vehicles is using table_name: '{table_name}'") # CHANGED: print to logger.debug
    return execute_read_query(table_name, conditions, limit) # No 'verbose' arg needed here now
