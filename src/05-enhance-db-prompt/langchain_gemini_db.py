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

from database_tool import get_table_schema, query_electric_vehicles, count_electric_vehicles
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

    tools = [research_document_store, get_table_schema, query_electric_vehicles, count_electric_vehicles]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are an AI assistant. You have access to a document store tool and an Oracle Database tool.\n"
             "**Your primary role is to answer questions about electric vehicles by interacting with the Oracle Database.**\n"
             "**When a user asks for specific data from the 'electricvehicles' table, you are capable of generating appropriate SQL query conditions on the fly to fulfill the request.**\n"
             "**ALWAYS use the `query_electric_vehicles` tool to execute these queries.** Do NOT execute SQL directly. "
             "**Remember the table name is 'electricvehicles' (all lowercase).**\n"
             "When using conditions (WHERE clause) for the `query_electric_vehicles` tool, ensure column names are correctly cased. If a column in Oracle was created with mixed or specific casing (e.g., 'Model', 'CITY'), you must enclose it in double quotes (e.g., `\"Model\" = 'Tesla'`) or use `UPPER()` on the column name (e.g., `UPPER(MAKE) = UPPER('TESLA')`). Prefer `UPPER()` for robustness when possible.\n"
             "First, use the `get_table_schema` tool to understand the table structure of 'electricvehicles' if you are unsure about its columns or need precise filtering information.\n"
             "Then, use the `query_electric_vehicles` tool to retrieve data from the 'electricvehicles' table. "
             "Provide relevant conditions (e.g., `MODEL = 'Tesla'`) and a `limit` if specified by the user.\n"
             "\n"
             "**IMPORTANT: When the user asks for the TOTAL NUMBER or COUNT of records, or asks 'how many' electric vehicles, you MUST use the `count_electric_vehicles` tool.** This tool is specifically designed to get the total count without retrieving all data.\n"
             "**Example for counting:**\n"
             "User: How many electric vehicles do you have?\n"
             "Agent will call: `count_electric_vehicles()`\n"
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
    # REMOVED: set_logging_level calls from here.
    # The root logging level is now managed solely by cli_chatbot.py

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
    # Initial logging setup for when this script is run directly for testing.
    # This captures logs from the start of execution.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Testing LangChain Agent with RAG and Dynamic Database Tools using Vertex AI integration...")
    logger.info("Ensure your VM's service account has 'Vertex AI User' role.")

    current_chat_history = []

    print("\n--- Test 1: General knowledge (INFO level) ---")
    user_input1 = "What is the capital of Brazil?"
    print(f"User: {user_input1}")
    res1, current_chat_history = get_gemini_response(user_input1, current_chat_history, verbose=False) # Pass verbose for LangChain's internal executor
    print(f"Bot: {res1}")

    print("\n--- Test 2: Question requiring the RAG tool (DEBUG level) ---")
    user_input2 = "Tell me about Python Flask framework."
    print(f"User: {user_input2}")
    res2, current_chat_history = get_gemini_response(user_input2, current_chat_history, verbose=True) # Pass verbose for LangChain's internal executor
    print(f"Bot: {res2}")

    print("\n--- Test 3: Question requiring the new Database Tool (Get Schema, DEBUG level) ---")
    user_input3 = "What columns are in the electricvehicles table?"
    print(f"User: {user_input3}")
    res3, current_chat_history = get_gemini_response(user_input3, current_chat_history, verbose=True) # Pass verbose for LangChain's internal executor
    print(f"Bot: {res3}")

    print("\n--- Test 4: Question requiring the new Database Tool (Dynamic Query, DEBUG level) ---")
    user_input4 = "Get me the Model and Make of 3 electric vehicles that are Teslas."
    print(f"User: {user_input4}")
    res4, current_chat_history = get_gemini_response(user_input4, current_chat_history, verbose=True) # Pass verbose for LangChain's internal executor
    print(f"Bot: {res4}")

    print("\n--- Test 5: Another RAG tool question with existing history (INFO level) ---")
    user_input5 = "What is RAG in AI?"
    print(f"User: {user_input5}")
    res5, current_chat_history = get_gemini_response(user_input5, current_chat_history, verbose=False) # Pass verbose for LangChain's internal executor
    print(f"Bot: {res5}")
