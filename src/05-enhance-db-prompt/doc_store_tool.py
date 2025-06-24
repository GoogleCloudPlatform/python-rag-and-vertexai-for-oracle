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

