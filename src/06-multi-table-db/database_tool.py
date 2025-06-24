# database_tool.py
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

# MODIFIED: Removed TABLE_METADATA import as it's now handled internally by database_utils
from database_utils import get_table_schema_string, get_engine, get_all_accessible_tables, DB_TABLE_OWNER_SCHEMA
from sqlalchemy import text

logger = logging.getLogger(__name__)

@tool
def get_table_schema(table_name: str) -> str:
    """
    Retrieves the schema (column names and data types) for a given database table.
    Use this tool BEFORE querying data from a table if you are unsure about its structure
    or the available columns for filtering.
    Input should be the exact table name, e.g., 'ELECTRICVEHICLES' or 'CUSTOMERS'.
    """
    logger.debug(f"Tool Call: get_table_schema for table: '{table_name}'")
    return get_table_schema_string(table_name)

@tool
def query_database(
    table_name: str,
    select_columns: str = "*",
    conditions: str = None,
    group_by_columns: str = None,
    order_by_columns: str = None,
    limit: int = None
) -> str:
    """
    Executes a flexible read query on the specified database table.
    This tool allows for dynamic construction of SQL queries including SELECT, WHERE, GROUP BY, and ORDER BY clauses.

    Args:
        table_name (str): The name of the table to query (e.g., 'ELECTRICVEHICLES', 'CUSTOMERS').
        select_columns (str): A comma-separated list of columns to select, including aggregate functions (e.g., 'MAKE, COUNT(*) AS MakeCount'). Defaults to '*'.
        conditions (str): An optional SQL WHERE clause (e.g., "UPPER(COUNTY) = UPPER('King') AND MODEL LIKE 'Tesla%'").
        group_by_columns (str): An optional comma-separated list of columns for the GROUP BY clause (e.g., 'MAKE'). Required if aggregate functions are used in select_columns.
        order_by_columns (str): An optional comma-separated list of columns for the ORDER BY clause (e.g., 'MakeCount DESC').
        limit (int): An optional integer to limit the number of rows returned.

    Returns:
        str: Results as a formatted string, typically a Markdown table.
    """
    logger.debug(f"Tool Call: query_database - Table: {table_name}, Select: {select_columns}, Conditions: {conditions}, GroupBy: {group_by_columns}, OrderBy: {order_by_columns}, Limit: {limit}")

    engine = get_engine()
    connection = None
    try:
        connection = engine.connect()

        query_string = f"SELECT {select_columns} FROM {table_name}"

        if conditions:
            query_string += f" WHERE {conditions}"

        if group_by_columns:
            query_string += f" GROUP BY {group_by_columns}"

        if order_by_columns:
            query_string += f" ORDER BY {order_by_columns}"

        if limit is not None and limit > 0:
            query_string = f"SELECT * FROM ({query_string}) WHERE ROWNUM <= {limit}"

        logger.debug(f"Executing dynamic SQL query: {query_string}")

        result = connection.execute(text(query_string))
        rows = result.fetchall()

        if not rows:
            logger.info(f"No data found for query: {query_string}")
            return f"No data found for the given criteria in {table_name}."

        column_names = result.keys()
        formatted_results = "| " + " | ".join(column_names) + " |\n"
        formatted_results += "| " + "---|" * len(column_names) + "\n"
        for row in rows:
            formatted_results += "| " + " | ".join(map(str, row)) + " |\n"

        logger.info(f"Query results for {table_name}:\n{formatted_results}")
        return formatted_results

    except Exception as e:
        logger.exception(f"Error executing dynamic query on {table_name}: {e}")
        return f"Error performing database query: {e}. Please check the query components."
    finally:
        if connection:
            connection.close()


@tool
def list_all_tables() -> str:
    """
    Lists all database tables accessible in the configured schema, along with their descriptions.
    Use this tool to discover what tables are available and what kind of data they contain.
    Returns a formatted string listing table names and their purposes.
    """
    logger.debug(f"Tool Call: list_all_tables for schema '{DB_TABLE_OWNER_SCHEMA}'")
    try:
        tables_info = get_all_accessible_tables(DB_TABLE_OWNER_SCHEMA) # Get list of dicts
        if tables_info:
            formatted_list = "Available Tables:\n"
            for table_info in tables_info:
                formatted_list += f"- **{table_info['name']}**: {table_info['description']}\n"
            logger.info(f"Accessible tables info:\n{formatted_list}")
            return formatted_list
        else:
            logger.warning("No accessible tables found.")
            return "No accessible tables found in the database for the configured user and schema."
    except Exception as e:
        logger.exception("Error listing all accessible tables.")
        return f"Error listing tables: {e}"
