#This project is intended for demonstration purposes only. It is not
#intended for use in a production environment.
#
#This is not an officially supported Google product. This project is not
#eligible for the [Google Open Source Software Vulnerability Rewards
#Program](https://bughunters.google.com/open-source-security).
#
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

## Getting Started

To get a copy of this project up and running on your local machine, follow these simple steps:

### Prerequisites

* **Git:** You need Git installed on your system. If you don't have it, you can download it from [git-scm.com](https://git-scm.com/downloads) or install it via your operating system's package manager (e.g., `sudo apt install git` on Ubuntu, `brew install git` on macOS).
* **SSH Key (Recommended for GitHub):** For more secure and convenient access to GitHub, it's recommended to set up an SSH key. If you haven't done this before, GitHub provides excellent guides:
    * [Generating a new SSH key and adding it to the ssh-agent](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
    * [Adding your SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
* **Oracle Database:** This code assumes you have an Oracle Database instance up and running. (A link to another document/video/blog for Oracle Database setup will be provided).

### Cloning the Repository

1.  **Open your terminal or command prompt.**
2.  **Navigate to the directory** where you want to save the project. For example: `cd ~/Documents/GitHub` (you can create this directory if it doesn't exist: `mkdir -p ~/Documents/GitHub`).
3.  **Clone the repository** using one of the following methods:

    **Option A: Using SSH (Recommended)**
    If you have set up your SSH key with GitHub, this method is more secure and generally easier for repeated access.
    ```bash
    git clone git@github.com:sam-gamare/genai-db-samples.git
    ```

    **Option B: Using HTTPS**
    If you haven't set up SSH keys, or prefer HTTPS, you can use this method. You might be prompted for your GitHub username and password (or a Personal Access Token if you have 2FA enabled).
    ```bash
    git clone [https://github.com/sam-gamare/genai-db-samples.git](https://github.com/sam-gamare/genai-db-samples.git)
    ```
4.  **Navigate into the cloned directory:**
    ```bash
    cd genai-db-samples
    ```


### Project Setup and Virtual Environment

Next, create a Python virtual environment to manage dependencies for this project.

1.  **Create the virtual environment**
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate it**
    ```bash
    source .venv/bin/activate
    ```

### Install Dependencies

Now that your virtual environment is active, install the necessary Python packages:

```bash
pip install langchain-google-vertexai -q
pip install google-generativeai langchain langchain-google-genai -q
pip install oracledb dotenv cx_Oracle -q
```


### Configure Environment Variables

Create a file named `.env` in the root of your project directory to store your database connection details securely.

1.  **Create `.env` file**: Open a text editor and create a new file named `.env` in the `genai-db-samples` directory.

2.  **Add variables**: Copy and paste the following into your `.env` file:
    ```
    DB_USER="ro_user"
    DB_PASSWORD="YourPassword"
    DB_DSN="<MachineName>:1521/<PDBName>"
    ```

3.  **Replace placeholders**: **Crucially, replace `"YourPassword"`, `<MachineName>`, and `<PDBName>` with your actual database password, machine name (or IP address), and Pluggable Database (PDB) name.** For example, `DB_DSN="localhost:1521/FREEPDB1"`.

### Database Users

Ensure you can log in as the following users in your Oracle Database:
* **`rw_user`**: For read/write operations (e.g., creating tables, loading data).
* **`ro_user`**: For read-only operations.

### Create Table

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

### Download Data

1.  **Get the data**: Download the electric vehicle population data from the official source:
    [https://catalog.data.gov/dataset/electric-vehicle-population-data](https://catalog.data.gov/dataset/electric-vehicle-population-data)

2.  **Save as CSV**: Make sure to save the downloaded data as a **.csv** file in your `genai-db-samples` directory.

### Import Data

Ideally execute this on the machine where Oracle DB is installed to make this faster and also supporting libraries are easily available.

1.  **Use SQL*Loader**: Import the downloaded CSV data into your Oracle database using the `sqlldr` utility.
    ```bash
    sqlldr rw_user@localhost:1521/FREEPDB1 CONTROL=Load_Electric_Vehicle_Population_Data.csv.ctl
    ```
    (Ensure `Load_Electric_Vehicle_Population_Data.csv.ctl` is correctly configured for your CSV file and located in the same directory where you run the command).

### Test Database Connection and Data

Finally, run the Python script to verify your database connection and confirm that data has been loaded correctly.

1.  **Execute the test script**
    ```bash
    python src/01-db-connection/db_connection_example.py
    ```
    This script should connect to your Oracle database using the details from your `.env` file and display a few rows from the `ElectricVehicles` table to the console.

### Test Langchain setup with VertexAI using Gemini

Run the python script to check if we can use VertexAI API using Gemini model. We also have a limited RAG function to inject additional data beyond what the model has been trained on. Remember this does not connect to Google Search for grounding data. We will do that at some point in the future

1.  **Execute the test script**
    ```bash
    python src/02-langchain-gemini-intro/langchain_gemini_rag_example.py
    ```
    This script is asking for some basic information to the LLM, like what is the capital of Brazil. This obviously the LLM should know as it has been pre-trained. However we are also going to inject our sample RAG data explicitly. Which means when it encounters a question specific to what our RAG data provides as prompt and answer, the LLM will now leverage the RAG data.




### Test Langchain setup with VertexAI using Gemini, but retrieve data using Oracle database

Run the python script to check if we can use VertexAI API using Gemini model and also retrieve data from Oracle database. 

1.  **Execute the test script**
    ```bash
    python src/03-langchain-gemini-with-data/langchain_gemini_db.py
    ```
    This script is asking for some basic information to the LLM, like what is the capital of Brazil. This obviously the LLM should know as it has been pre-trained. However we are also going to inject our sample RAG data explicitly. Which means when it encounters a question specific to what our RAG data provides as prompt and answer, the LLM will now leverage the RAG data.


### Test command line chatbot

Run the python script to check if we can use VertexAI API using Gemini model and also retrieve data from Oracle database. Note for simplicity we have copied all the files explicitly in each sub-example

1.  **Execute the test script**
    ```bash
    python src/04-cli-chatbo/cli_chatbot.py
    ```
    This chatbot should allow us to interactively type questions and get answers from the chatbot. 



### Enhancing Tool Usability (Dynamic Arguments & Schema Retrieval)

This step significantly enhances the database integration by:
* Implementing dynamic queries to the `ElectricVehicles` table using SQLAlchemy.
* Introducing a new `get_table_schema` tool, allowing the LangChain agent to dynamically retrieve table structures.
* Updating the LLM's prompt to guide it to use `get_table_schema` before attempting complex data queries, ensuring it understands the available columns for filtering.

1.  **Execute the test script for combined tools**
    ```bash
    python src/05-enhance-db-prompt/langchain_gemini_db.py
    ```
    This script will now demonstrate:
    * Asking about general knowledge.
    * Using the RAG tool.
    * **New:** Asking about "What columns are in the ElectricVehicles table?" which should trigger the `get_table_schema` tool.
    * **New:** Asking for specific data like "Get me the Model and Make of 3 electric vehicles that are Teslas." which should trigger the `query_electric_vehicles` tool with dynamic arguments.

2.  **Use the command-line chatbot**
    ```bash
    python src/05-enhance-db-prompt/cli_chatbot.py
    ```
    Interact with the chatbot. Try asking questions that require database interaction, such as:
    * "What information can you give me about electric vehicles?" (Might trigger schema or initial few rows)
    * "Show me the columns for the ElectricVehicles table."
    * "Find all electric vehicles made by Nissan."
    * "List 10 electric vehicles with 'LEAF' in their model name."
