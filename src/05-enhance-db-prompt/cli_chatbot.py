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
import logging # ADDED: Import logging

# Adjust the import path based on your project structure
# We'll import get_gemini_response and also the set_logging_level function from langchain_gemini_db
from langchain_gemini_db import get_gemini_response, set_logging_level # MODIFIED: Added set_logging_level import

# Configure basic logging for the entire application at its entry point.
# This ensures that log messages are captured from the very beginning.
# Set initial level to INFO (only INFO and above will show by default).
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
cli_logger = logging.getLogger(__name__) # ADDED: Logger for CLI specific messages

def run_chatbot():
    """
    Runs a command-line interface chatbot for interactive questions.
    Allows dynamic control of verbose output.
    """
    print("Welcome to the Gemini-powered Chatbot with Database & RAG Tools!")
    print("You can ask about internal documents or query the 'electricvehicles' table.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("You can also type 'Turn verbose on' or 'Turn verbose off' to control debug output.")
    print("You can also type 'Turn verbose on will set it to INFO' or 'Turn verbose off will set it to ERROR' to control debug output.")

    set_logging_level("ERROR") # Ensure initial state is ERROR at start of chatbot

    current_chat_history = []

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            cli_logger.info("Chatbot session ended by user.") # CHANGED: print to logger.info
            print("Chatbot: Goodbye!") # User-facing print
            break
        elif user_input.lower() == "turn verbose on":
            current_verbose_state = True
            set_logging_level("DEBUG") # Set root logger to DEBUG
            print("Chatbot: Verbose output is now ENABLED. You will see more detailed logs.") # User-facing print
            continue # Don't send this command to the LLM
        elif user_input.lower() == "turn verbose off":
            current_verbose_state = False
            set_logging_level("INFO") # Set root logger back to INFO
            print("Chatbot: Verbose output is now DISABLED. Only important messages will be shown.") # User-facing print
            continue # Don't send this command to the LLM

        try:
            # The verbose parameter here is still passed to get_gemini_response,
            # which in turn passes it to AgentExecutor's internal verbose flag.
            # Our custom logging level is set by set_logging_level above.
            response_text, updated_history = get_gemini_response(user_input, current_chat_history, verbose=current_verbose_state)
            print(f"Chatbot: {response_text}") # User-facing print
            current_chat_history = updated_history
        except Exception as e:
            cli_logger.exception("Chatbot Error: An unexpected error occurred.") # CHANGED: print to logger.exception
            print(f"Chatbot Error: An unexpected error occurred: {e}") # User-facing error print
            print("Please try again.") # User-facing print

if __name__ == '__main__':
    run_chatbot()
