# cli_chatbot.py
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
import sys
import logging

from langchain_gemini_db import get_gemini_response, set_logging_level

# MODIFIED: Set initial level to ERROR in basicConfig for minimal output at startup
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
cli_logger = logging.getLogger(__name__)

def run_chatbot():
    """
    Runs a command-line interface chatbot for interactive questions.
    Allows dynamic control of verbose output.
    """
    print("Welcome to the Gemini-powered Chatbot with Database & RAG Tools!")
    print("You can ask about internal documents or query the 'electricvehicles' table.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("You can also type 'Turn verbose on' or 'Turn verbose off' to control debug output.")
    print("Verbose: 'on' sets to DEBUG, 'off' sets to ERROR (minimal).") # MODIFIED: Clarified output levels

    # MODIFIED: Ensure initial state is ERROR (minimal) at start of chatbot
    set_logging_level("ERROR") # Sets the root logger level

    current_chat_history = []

    # Determine initial LangChain verbose setting based on the global logger level
    # If the global level is INFO or DEBUG, we consider it "verbose enough" for LangChain's internal executor
    langchain_executor_verbose = True if logging.getLogger().level <= logging.INFO else False


    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            cli_logger.info("Chatbot session ended by user.")
            print("Chatbot: Goodbye!")
            break
        elif user_input.lower() == "turn verbose on":
            set_logging_level("DEBUG") # Set root logger to DEBUG
            langchain_executor_verbose = True # Also enable LangChain's internal verbose
            print("Chatbot: Verbose output is now ENABLED. You will see detailed DEBUG logs.")
            continue
        elif user_input.lower() == "turn verbose off":
            set_logging_level("ERROR") # Set root logger back to ERROR (minimal)
            langchain_executor_verbose = False # Also disable LangChain's internal verbose
            print("Chatbot: Verbose output is now DISABLED. Only ERROR and CRITICAL messages will be shown.")
            continue

        try:
            # Pass the langchain_executor_verbose state directly to get_gemini_response
            response_text, updated_history = get_gemini_response(user_input, current_chat_history, verbose=langchain_executor_verbose)
            print(f"Chatbot: {response_text}")
            current_chat_history = updated_history
        except Exception as e:
            cli_logger.exception("Chatbot Error: An unexpected error occurred.")
            print(f"Chatbot Error: An unexpected error occurred: {e}")
            print("Please try again.")

if __name__ == '__main__':
    run_chatbot()
