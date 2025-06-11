# genai-db-samples
# Author: Sam Gamare [ Google ]
# Initiated on: Jun 10, 2025

The content is designed to be an incremental follow-along, reflecting the process by which the code was developed

The flow of incremental code development followed :
* Establishing Database Baseline: Initiated with basic code to confirm database connection functionality.
* Connecting to Generative AI: Set up a LangChain invocation layer to interact with Vertex AI APIs powered by Gemini.
* First Database Tool (Proof of Concept): Integrated a LangChain Tool for direct calls to the ElectricVehicles database, starting with a limited, hardcoded data consumption to prove the concept.
* Enabling User Interaction: Developed a command-line chatbot to facilitate asking incremental questions.
* Enhancing Tool Usability: Fine-tuned prompts to allow for dynamic arguments to be passed effectively to the integrated functions.
* Expanding Toolset: Included another LangChain Tool to provide real-time currency conversion capabilities.

---

## How to Clone this Repository

To get started, please refer to the comprehensive [Git Setup Guide](README-git-setup.md) for detailed instructions on cloning this repository.

## Setup Instructions

This code assumes you have an Oracle Database instance up and running.
<Will post  Link to another document / video / blog for Oracle Database setup>

### 1. Get the Project

Start by cloning the repository to your local machine.

1.  **Clone the repository**
    ```bash
    git clone https://[https://github.com/your-username/genai-db-samples.git](https://github.com/your-username/genai-db-samples.git)
    # Replace 'your-username' with the actual GitHub username or organization
    # if this repository is hosted publicly.
    ```

2.  **Navigate into the project directory**
    ```bash
    cd genai-db-samples
    ```

### 2. Project Setup and Virtual Environment

Next, create a Python virtual environment to manage dependencies for this project.

1.  **Create the virtual environment**
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate it**
    ```bash
    source .venv/bin/activate
    ```

### 3. Install Dependencies

Now that your virtual environment is active, install the necessary Python packages:

```bash
pip install langchain-google-vertexai -q
pip install google-generativeai langchain langchain-google-genai -q
pip install oracledb dotenv cx_Oracle -q
```


### 4. Configure Environment Variables

Create a file named `.env` in the root of your project directory to store your database connection details securely.

1.  **Create `.env` file**: Open a text editor and create a new file named `.env` in the `genai-db-samples` directory.

2.  **Add variables**: Copy and paste the following into your `.env` file:
    ```
    DB_USER="ro_user"
    DB_PASSWORD="YourPassword"
    DB_DSN="<MachineName>:1521/<PDBName>"
    ```

3.  **Replace placeholders**: **Crucially, replace `"YourPassword"`, `<MachineName>`, and `<PDBName>` with your actual database password, machine name (or IP address), and Pluggable Database (PDB) name.** For example, `DB_DSN="localhost:1521/FREEPDB1"`.

### 5. Database Users

Ensure you can log in as the following users in your Oracle Database:
* **`rw_user`**: For read/write operations (e.g., creating tables, loading data).
* **`ro_user`**: For read-only operations.

### 6. Create Table

1.  **Log in as `rw_user`**: Use `sqlplus` to connect to your Oracle database.
    ```bash
    sqlplus rw_user@localhost:1521/FREEPDB1
    ```
    (Adjust `localhost:1521/FREEPDB1` to your specific database connection string if different).

2.  **Run the table creation script**: Execute the `create-table-electric-vehicles.sql` script.
    ```sql
    -- Inside sqlplus
    @create-table-electric-vehicles.sql
    ```

### 7. Download Data

1.  **Get the data**: Download the electric vehicle population data from the official source:
    [https://catalog.data.gov/dataset/electric-vehicle-population-data](https://catalog.data.gov/dataset/electric-vehicle-population-data)

2.  **Save as CSV**: Make sure to save the downloaded data as a **.csv** file in your `genai-db-samples` directory.

### 8. Import Data

1.  **Use SQL*Loader**: Import the downloaded CSV data into your Oracle database using the `sqlldr` utility.
    ```bash
    sqlldr rw_user@localhost:1521/FREEPDB1 CONTROL=Load_Electric_Vehicle_Population_Data.csv.ctl
    ```
    (Ensure `Load_Electric_Vehicle_Population_Data.csv.ctl` is correctly configured for your CSV file and located in the same directory where you run the command).

### 9. Test Database Connection and Data

Finally, run the Python script to verify your database connection and confirm that data has been loaded correctly.

1.  **Execute the test script**
    ```bash
    python src/01-db-connection/db_connection_example.py
    ```
    This script should connect to your Oracle database using the details from your `.env` file and display a few rows from the `ElectricVehicles` table to the console.

### 10. Test Langchain setup with VertexAI using Gemini 

Run the python script to check if we can use VertexAI API using Gemini model. We also have a limited RAG function to inject additional data beyond what the model has been trained on. Remember this does not connect to Google Search for grounding data. We will do that at some point in the future

1. ** Execute the script **
    ```bash
    python src/02-langchain-gemini-intro/simple_langchain_gemini.py
    ```
    This script is asking for some basic information to the LLM, like what is the capital of Brazil. This the LLM should know as it has been pre-trained. However we are also injected our RAG data specifically. Which means when it encounters a question specific to what our RAG data provides as prompt and answer, the LLM will now leverage the RAG data.

