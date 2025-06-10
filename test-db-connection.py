import oracledb
import getpass
import os
from dotenv import load_dotenv

#Load values from .env file
load_dotenv()

print(f"Looking for .env in: {os.path.join(os.getcwd(), '.env')}")

# --- Configuration ---
# Get connection details from environment variables
# os.getenv() retrieves the value of the environment variable.
# It returns None if the variable is not found, so good to provide defaults or handle.
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
dsn = os.getenv("DB_DSN")

print(f"Attempting to connect as user: {user}")

# You can still use getpass if you want to fall back to interactive input
# if the environment variable is not set.
if not password:
    password = getpass.getpass("Enter DB password (not found in .env or env var): ")

# --- Input Validation (Recommended) ---
if not all([user, password, dsn]):
    print("Error: Missing one or more database connection environment variables.")
    print("Please ensure DB_USER, DB_PASSWORD, and DB_DSN are set in your .env file or environment.")
    exit(1) # Exit the script if critical info is missing

# --- Connection and Query Execution ---
connection = None
cursor = None

try:
    print(f"Attempting to connect as user: {user}")
    print(f"Attempting to connect to DSN: {dsn}")

    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    print("Connected to Oracle Database!")

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ElectricVehicles WHERE ROWNUM <5 ")  # Replace your_table

    for row in cursor:
        print(row)

except oracledb.Error as e:
    print(f"Error: {e}")

finally:
    if connection:
        cursor.close()
        connection.close()
        print("Connection closed.")
