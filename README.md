# genai-db-samples

This repository contains samples for interacting with databases using generative AI.

---

## Setup Instructions

This code assumes you have an Oracle Database instance up and running.

### Database Users

Ensure you can log in as the following users:
* `rw_user`: For read/write operations (e.g., creating tables, loading data).
* `ro_user`: For read-only operations.

### Create Table

1.  **Log in as `rw_user`**: Use `sqlplus` to connect to your Oracle database.
    ```bash
    sqlplus rw_user@localhost:1521/FREEPDB1
    ```
    (Adjust `localhost:1521/FREEPDB1` to your database connection string if different).

2.  **Run the table creation script**: Execute the `create-table-electric-vehicles.sql` script.
    ```sql
    -- Inside sqlplus
    @create-table-electric-vehicles.sql
    ```

### Download Data

1.  **Get the data**: Download the electric vehicle population data from the official source:
    [https://catalog.data.gov/dataset/electric-vehicle-population-data](https://catalog.data.gov/dataset/electric-vehicle-population-data)

2.  **Save as CSV**: Make sure to save the downloaded data as a **.csv** file.

### Import Data

1.  **Use SQL*Loader**: Import the downloaded CSV data into your Oracle database using the `sqlldr` utility.
    ```bash
    sqlldr rw_user@localhost:1521/FREEPDB1 CONTROL=Load_Electric_Vehicle_Population_Data.csv.ctl
    ```
    (Ensure `Load_Electric_Vehicle_Population_Data.csv.ctl` is correctly configured for your CSV file).
