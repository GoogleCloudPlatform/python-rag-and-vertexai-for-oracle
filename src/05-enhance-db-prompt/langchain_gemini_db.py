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
from langchain.tools import tool # Still needed for research_document_store if kept

import os
from dotenv import load_dotenv

# --- UPDATED IMPORTS for your database tools ---
# Make sure to import both tools from database_tool.py
from database_tool import get_electric_vehicles_data # OLD - will replace with query_electric_vehicles
from database_tool import get_table_schema, query_electric_vehicles # NEW

#Load values from .env file
load_dotenv()

print(f"Looking for .env in: {os.path.join(os.getcwd(), '.env')}")

# --- Configuration ---
projectid = os.getenv("GCP_PROJECT_ID")
gcpregion = os.getenv("GCP_REGION")

# --- Dummy RAG Tool Implementation (Keep as is) ---
@tool
def research_document_store(query: str) -> str:
    """
    Searches an internal document store or knowledge base for information.
    """
    print(f"\n--- Tool Call: research_document_store with query: '{query}' ---")
    query = query.lower()

    if "python" in query and "flask" in query:
        return "Flask is a lightweight Python web framework for building web applications. It's known for its simplicity and flexibility, making it a good choice for smaller projects and APIs. It uses Jinja2 for templating and Werkzeug for WSGI utilities."
    elif "gemini api" in query or "google ai studio" in query:
        return "The Gemini API allows developers to access Google's large language models. It's often used via the `google-generativeai` library or through frameworks like LangChain. Google AI Studio is a web-based tool to prototype with Gemini models."
    elif "rag" in query or "retrieval augmented generation" in query:
        return "Retrieval-Augmented Generation (RAG) is an AI framework that retrieves facts from an external knowledge base to ground large language models (LLMs) on the most accurate and up-to-date information. This helps reduce hallucinations and provides specific, verifiable answers. It involves a retrieval component (the 'Tool' here) and a generation component (the LLM)."
    elif "linux vm" in query or "virtual machine" in query:
        return "A Linux VM (Virtual Machine) provides a virtualized operating system environment running on top of physical hardware. It allows you to run Linux alongside other operating systems or to isolate environments for development and deployment. Common uses include hosting web applications, databases, or development servers."
    elif "tool" in query and ("langchain" in query or "agent" in query):
        return "In LangChain, a 'Tool' is an interface that an agent can use to interact with the world. This could be anything from searching the internet, calling a custom API, interacting with a database, or, in the context of RAG, retrieving information from a specific knowledge base. Agents learn to use tools based on their descriptions and the prompt provided."
    else:
        return "No specific information found related to your query in the document store. Please try rephrasing or asking about a different topic."


def setup_langchain_agent():
    """
    Configures the LangChain agent with the Gemini model on Vertex AI and custom tools.
    This function leverages Application Default Credentials (ADC).
    Ensure your GCE VM's service account has the 'Vertex AI User' role.
    """
    project_id = projectid
    location = gcpregion


    llm = ChatVertexAI(
        model_name="gemini-2.0-flash",
        temperature=0,
        # project=project_id, # Uncomment and set if needed
        # location=location,  # Uncomment and set if needed
    )

    # --- KEY CHANGE: Add both new database tools here ---
    tools = [research_document_store, get_table_schema, query_electric_vehicles]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are an AI assistant. You have access to a document store tool and an Oracle Database tool.\n"
             "When asked about database information, first use the `get_table_schema` tool to understand the table structure of 'ElectricVehicles' if you are unsure or need column names.\n"
             "Then, use the `query_electric_vehicles` tool to retrieve data from the 'ElectricVehicles' table. "
             "Provide relevant conditions (e.g., `MODEL = 'Tesla'`) and a `limit` if specified by the user.\n"
             "Use the document store for other internal document questions. If a question is general knowledge, answer directly.\n"
             "Always present tool responses clearly in your answer."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor


def get_gemini_response(prompt_text, chat_history=None):
    """
    Sends a prompt to the LangChain agent and returns the text response.
    Maintains chat history for multi-turn conversations.
    """
    try:
        agent_executor = setup_langchain_agent()
    except Exception as e:
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
        print(f"LangChain Agent Error: {e}")
        return f"Error processing your request: {e}. Please try again.", chat_history


if __name__ == '__main__':
    print("Testing LangChain Agent with RAG and Dynamic Database Tools using Vertex AI integration...")
    print("Ensure your VM's service account has 'Vertex AI User' role.")

    current_chat_history = []

    print("\n--- Test 1: General knowledge ---")
    user_input1 = "What is the capital of Brazil?"
    print(f"User: {user_input1}")
    res1, current_chat_history = get_gemini_response(user_input1, current_chat_history)
    print(f"Bot: {res1}")

    print("\n--- Test 2: Question requiring the RAG tool ---")
    user_input2 = "Tell me about Flask framework."
    print(f"User: {user_input2}")
    res2, current_chat_history = get_gemini_response(user_input2, current_chat_history)
    print(f"Bot: {res2}")

    print("\n--- Test 3: Question requiring the new Database Tool (Get Schema) ---")
    user_input3 = "What columns are in the ElectricVehicles table?"
    print(f"User: {user_input3}")
    res3, current_chat_history = get_gemini_response(user_input3, current_chat_history)
    print(f"Bot: {res3}")

    print("\n--- Test 4: Question requiring the new Database Tool (Dynamic Query) ---")
    user_input4 = "Get me the Model and Make of 3 electric vehicles that are Teslas."
    print(f"User: {user_input4}")
    res4, current_chat_history = get_gemini_response(user_input4, current_chat_history)
    print(f"Bot: {res4}")

    print("\n--- Test 5: Another RAG tool question with existing history ---")
    user_input5 = "What is RAG in AI?"
    print(f"User: {user_input5}")
    res5, current_chat_history = get_gemini_response(user_input5, current_chat_history)
    print(f"Bot: {res5}")
