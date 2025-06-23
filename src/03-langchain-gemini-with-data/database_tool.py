
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
from langchain.tools import tool

# Load values from .env file
load_dotenv()

# Get connection details from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# --- Helper function for database connection ---
def _get_db_connection():
    """Establishes and returns an Oracle Database connection."""
    if not all([DB_USER, DB_PASSWORD, DB_DSN]):
        raise ValueError("Database connection details (DB_USER, DB_PASSWORD, DB_DSN) not found in environment variables.")
    try:
        connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        return connection
    except oracledb.Error as e:
        raise ConnectionError(f"Failed to connect to Oracle Database: {e}")

@tool
def get_electric_vehicles_data(query: str = None) -> str:
    """
    Retrieves a limited set of data from the ElectricVehicles table in the Oracle Database.
    This tool performs a hardcoded query for proof of concept.
    In future iterations, this tool could take dynamic parameters.
    """
    print(f"\n--- Tool Call: get_electric_vehicles_data ---")
    connection = None
    cursor = None
    results = []

    try:
        connection = _get_db_connection()
        cursor = connection.cursor()

        # Hardcoded query for proof of concept
        # You might want to select specific columns or add a WHERE clause
        # For POC, let's get a few rows and specific columns to keep output manageable
        cursor.execute("SELECT * FROM ElectricVehicles WHERE ROWNUM <= 5")

        for row in cursor:
            results.append(str(row[0])) # Convert tuple to string

        if results:
            return "Retrieved data from ElectricVehicles table:\n" + "\n".join(results)
        else:
            return "No data found in ElectricVehicles table for the hardcoded query."

    except (oracledb.Error, ConnectionError, ValueError) as e:
        return f"Error accessing database: {e}"
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# You can add a simple test block here if you want to run this file directly
if __name__ == '__main__':
    print("Testing get_electric_vehicles_data tool directly...")
    data_output = get_electric_vehicles_data()
    print(data_output)
