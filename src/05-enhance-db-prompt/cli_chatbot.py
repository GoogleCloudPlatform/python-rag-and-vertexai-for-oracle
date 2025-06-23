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

# Adjust the import path based on your project structure
from langchain_gemini_db import get_gemini_response # Your combined agent script


def run_chatbot():
    """
    Runs a command-line interface chatbot for interactive questions.
    """
    print("Welcome to the Gemini-powered Chatbot with Database & RAG Tools!")
    print("Type 'exit' or 'quit' to end the conversation.")

    current_chat_history = []

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break

        try:
            # Call the function that interacts with the LangChain agent
            response_text, updated_history = get_gemini_response(user_input, current_chat_history)
            print(f"Chatbot: {response_text}")
            current_chat_history = updated_history
        except Exception as e:
            print(f"Chatbot Error: An unexpected error occurred: {e}")
            print("Please try again.")

if __name__ == '__main__':
    run_chatbot()
