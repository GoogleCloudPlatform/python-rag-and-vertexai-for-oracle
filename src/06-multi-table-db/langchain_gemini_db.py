# langchain_gemini_db.py
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
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent

import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

from database_tool import get_table_schema, query_database, list_all_tables
from doc_store_tool import research_document_store

load_dotenv()

logger.debug(f"Looking for .env in: {os.path.join(os.getcwd(), '.env')}")

projectid = os.getenv("GCP_PROJECT_ID")
gcpregion = os.getenv("GCP_REGION")

def set_logging_level(level):
    """Sets the logging level for the root logger.
    Args:
        level (str): The desired logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    logging.getLogger().setLevel(numeric_level)
    logger.info(f"Root logging level set to {level.upper()}")


def setup_langchain_agent(verbose_langchain_executor: bool = False):
    """
    Configures the LangChain agent with the Gemini model on Vertex AI and custom tools.
    This function leverages Application Default Credentials (ADC).
    Ensure your GCE VM's service account has the 'Vertex AI User' role.
    The `verbose_langchain_executor` flag controls LangChain's internal verbosity.
    """
    project_id = projectid
    location = gcpregion

    llm = ChatVertexAI(
        model_name="gemini-2.0-flash",
        temperature=0,
        # project=project_id, # Uncomment and set if needed
        # location=location,  # Uncomment and set if needed
    )

    tools = [research_document_store, list_all_tables, get_table_schema, query_database]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are an AI assistant. You have access to a document store tool and an Oracle Database tool.\n"
             "**Your primary role is to answer questions about data within the Oracle Database using the available tools.**\n"
             "You can interact with multiple tables in the database. Use your knowledge to infer the correct table based on the user's query.\n"

             "**CRITICAL TOOL USAGE GUIDANCE:**\n"
             "1. **Always Start with Discovery or Schema Inspection for Database Queries:**\n"
             "   - **`list_all_tables()`:** If the user asks about available data, 'what tables do you have?', 'list tables', or if you are at the beginning of a conversation and the user's query *might* involve a table (but doesn't specify one), **you MUST first call `list_all_tables()` to understand the available tables and their descriptions.**\n"
             "   - **`get_table_schema(table_name)`:** Once you identify a potential table, or if the user asks directly about columns or structure of a table (e.g., 'What columns are in X table?'), **you MUST immediately call `get_table_schema(table_name)` for that table.** This is paramount to understand its exact column names, data types, and ensure correct query formulation. **NEVER assume column names or data types; always rely on the output of `get_table_schema`.**\n"
             "   - **Proceed to `query_database` only AFTER understanding the schema.**\n"

             "2. **Querying Data (`query_database`):** Use the `query_database` tool for ALL data operations: retrieving records, counting records, and performing aggregations (like finding most common items, or earliest/latest dates/timestamps). Do NOT execute SQL directly. Always pass components to the `query_database` tool's parameters.\n"
             "   - **Crucial for `query_database` parameters:** When constructing `select_columns`, `conditions`, `group_by_columns`, or `order_by_columns`, **you MUST use the exact column names and consider their data types as obtained from the `get_table_schema` tool.** Do not guess or invent column names.\n"

             "**Handling Table Ambiguity or Unknown Tables:**\n"
             "If you receive a user query that implies a table you don't recognize or that could map to multiple tables (even after using `list_all_tables`), you **MUST** ask the user for clarification. For example: 'I found tables X, Y, and Z that might contain that information. Which one are you interested in?' Or 'I'm not sure which table you mean by [user's ambiguous term]. Could you please specify a table from the list I can access?'\n"
             "\n"
             "**Key parameters for `query_database`:**\n"
             "- `table_name`: The name of the table to query (e.g., 'ELECTRICVEHICLES', 'CUSTOMERS', 'ORDERS'). Use the exact casing as provided by `list_all_tables` or `get_table_schema` output.\n"
             "- `select_columns`: A comma-separated list of columns to select, including aggregate functions (e.g., 'MAKE, COUNT(*) AS MakeCount', 'MIN(QUOTE_DATE) AS EarliestDate', 'MAX(STARTED_AT) AS LatestTripStart'). Default is '*'.\n"
             "- `conditions`: An optional SQL WHERE clause. When comparing strings (VARCHAR2), use single quotes (e.g., \"QUOTE_SYMBOL = 'GOOG'\"). For partial matches, use LIKE (e.g., \"MODEL LIKE 'Tesla%'\"). For dates/timestamps, use `TO_DATE('YYYY-MM-DD', 'YYYY-MM-DD')` or `TO_TIMESTAMP('YYYY-MM-DD HH24:MI:SS', 'YYYY-MM-DD HH24:MI:SS')` as needed. \n"
             "- `group_by_columns`: An optional comma-separated list of columns for the GROUP BY clause (e.g., 'MAKE'). Required if aggregate functions are used in `select_columns`.\n"
             "- `order_by_columns`: An optional comma-separated list of columns for the ORDER BY clause (e.g., 'MakeCount DESC').\n"
             "- `limit`: An optional integer to limit the number of rows returned.\n"
             "\n"
             "**Important Casing Rule for Columns in Conditions/Grouping:** If a column in Oracle was created with mixed or specific casing, you must use `UPPER()` on the column name (e.g., `UPPER(COUNTY) = UPPER('King')`). Use single quotes for string *values* within conditions.\n"
             "\n"
             "**Examples for `query_database` tool usage (always using column names from `get_table_schema` output):**\n"
             "1. **Retrieve all records (limited) from any table:**\n"
             "   User: Show me 5 records from the CUSTOMERS table.\n"
             "   Agent will call: `query_database(table_name=\"CUSTOMERS\", limit=5)`\n"
             "2. **Count all records from a table:**\n"
             "   User: How many electric vehicle records do you have?\n"
             "   Agent will call: `query_database(table_name=\"ELECTRICVEHICLES\", select_columns=\"COUNT(*) AS TotalRecords\")`\n"
             "3. **Count records with conditions:**\n"
             "   User: How many Tesla Model cars are registered?\n"
             "   Agent will call: `query_database(table_name=\"ELECTRICVEHICLES\", select_columns=\"COUNT(*) AS TeslaCount\", conditions=\"MODEL LIKE 'Tesla%' OR MAKE = 'TESLA'\")`\n"
             "4. **Get common makes by location (with count):**\n"
             "   User: What are the most common electric vehicle makes registered in King County, Washington? Provide count. Show tabular layout please.\n"
             "   Agent will call: `query_database(table_name=\"ELECTRICVEHICLES\", select_columns=\"MAKE, COUNT(*) AS VehicleCount\", conditions=\"UPPER(COUNTY) = UPPER('King') AND UPPER(STATE) = UPPER('WA')\", group_by_columns=\"MAKE\", order_by_columns=\"VehicleCount DESC\", limit=5)`\n"
             "5. **Retrieve specific columns with conditions:**\n"
             "   User: Show me the VIN and Make for 3 electric vehicles in Seattle.\n"
             "   Agent will call: `query_database(table_name=\"ELECTRICVEHICLES\", select_columns=\"VIN, MAKE\", conditions=\"UPPER(CITY) = UPPER('Seattle')\", limit=3)`\n"
             "6. **Find earliest/latest date/timestamp in a table:**\n"
             "   User: What is the earliest date you have for Stock Quotes?\n"
             "   Agent will call: `query_database(table_name=\"STOCKQUOTES\", select_columns=\"MIN(QUOTE_DATE) AS EarliestDate\")`\n"
             "   User: What is the latest bike trip start time?\n"
             "   Agent will call: `query_database(table_name=\"CITI_BIKE\", select_columns=\"MAX(STARTED_AT) AS LatestStartTime\")`\n"
             "   User: Show me stock quotes for GOOG on 2024-01-15.\n"
             "   Agent will call: `query_database(table_name=\"STOCKQUOTES\", conditions=\"QUOTE_SYMBOL = 'GOOG' AND QUOTE_DATE = TO_DATE('2024-01-15', 'YYYY-MM-DD')\")`\n"
             "\n"
             "Use the document store (`research_document_store`) for other internal document questions. If a question is general knowledge, answer directly.\n"
             "Always present tool responses clearly in your answer."

            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose_langchain_executor)

    return agent_executor


def get_gemini_response(prompt_text, chat_history=None, verbose: bool = False):
    """
    Sends a prompt to the LangChain agent and returns the text response.
    Maintains chat history for multi-turn conversations.
    The `verbose` flag controls LangChain's internal agent verbosity.
    """
    logger.debug("get_gemini_response called. LangChain internal verbose set to: %s", verbose)

    try:
        agent_executor = setup_langchain_agent(verbose_langchain_executor=verbose)
    except Exception as e:
        logger.exception("Configuration Error during agent setup.")
        return f"Configuration Error: {e}. Please ensure your VM has the correct service account and permissions (Vertex AI User role) and that your project/location are correctly configured if needed.", []

    lc_chat_history = []
    if chat_history:
        for turn in chat_history:
            if turn['role'] == 'human':
                lc_chat_history.append(HumanMessage(content=turn['parts'][0]['text']))
            elif turn['role'] == 'model':
                lc_chat_history.append(AIMessage(content=turn['parts'][0]['text']))

    try:
        response = agent_executor.invoke({
            "input": prompt_text,
            "chat_history": lc_chat_history
        })

        response_text = response['output']

        updated_history = list(chat_history) if chat_history else []
        updated_history.append({"role": "human", "parts": [{"text": prompt_text}]})
        updated_history.append({"role": "model", "parts": [{"text": response_text}]})

        return response_text, updated_history

    except Exception as e:
        logger.exception(f"LangChain Agent Error: {e}")
        return f"Error processing your request: {e}. Please try again.", chat_history


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Testing LangChain Agent with RAG and Dynamic Database Tools using Vertex AI integration...")
    logger.info("Ensure your VM's service account has 'Vertex AI User' role.")

    current_chat_history = []

    print("\n--- Test 1: General knowledge (INFO level) ---")
    user_input1 = "What is the capital of Brazil?"
    print(f"User: {user_input1}")
    res1, current_chat_history = get_gemini_response(user_input1, current_chat_history, verbose=False)
    print(f"Bot: {res1}")

    print("\n--- Test 2: Question requiring the RAG tool (DEBUG level) ---")
    user_input2 = "Tell me about Python Flask framework."
    print(f"User: {user_input2}")
    res2, current_chat_history = get_gemini_response(user_input2, current_chat_history, verbose=True)
    print(f"Bot: {res2}")

    print("\n--- Test 3: Question requiring the new Database Tool (Get Schema, DEBUG level) ---")
    user_input3 = "What columns are in the electricvehicles table?"
    print(f"User: {user_input3}")
    res3, current_chat_history = get_gemini_response(user_input3, current_chat_history, verbose=True)
    print(f"Bot: {res3}")

    print("\n--- Test 4: Question requiring the new Database Tool (Dynamic Query, DEBUG level) ---")
    user_input4 = "Get me the Model and Make of 3 electric vehicles that are Teslas."
    print(f"User: {user_input4}")
    res4, current_chat_history = get_gemini_response(user_input4, current_chat_history, verbose=True)
    print(f"Bot: {res4}")

    print("\n--- Test 5: Another RAG tool question with existing history (INFO level) ---")
    user_input5 = "What is RAG in AI?"
    print(f"User: {user_input5}")
    res5, current_chat_history = get_gemini_response(user_input5, current_chat_history, verbose=False)
    print(f"Bot: {res5}")

    print("\n--- Test 6: Question requiring multiple database queries with explicit guidance for discovery (DEBUG level) ---")
    # This simulates the user's successful direct instruction
    user_input6 = "On Sep-12-2023 what was the value of SPY. Also how many rides were taken on that day ?"
    print(f"User: {user_input6}")
    res6, current_chat_history = get_gemini_response(user_input6, current_chat_history, verbose=True)
    print(f"Bot: {res6}")

    print("\n--- Test 7: Confirming schema of STOCKQUOTES after previous interactions (DEBUG level) ---")
    user_input7 = "What columns are in the StockQuotes table?"
    print(f"User: {user_input7}")
    res7, current_chat_history = get_gemini_response(user_input7, current_chat_history, verbose=True)
    print(f"Bot: {res7}")

    print("\n--- Test 8: Confirming schema of CITI_BIKE after previous interactions (DEBUG level) ---")
    user_input8 = "What columns are in the Citi_Bike table?"
    print(f"User: {user_input8}")
    res8, current_chat_history = get_gemini_response(user_input8, current_chat_history, verbose=True)
    print(f"Bot: {res8}")
