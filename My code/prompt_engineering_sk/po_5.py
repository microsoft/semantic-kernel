import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
import semantic_kernel as sk

load_dotenv('var.env')
key = os.getenv('OPENAI_API_KEY')

kernel = sk.Kernel()
kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))


async def main():
    history = []  # Initialize history as an empty list

    while True:
        request = input("Your request: ")

        if request.upper() == "EXIT":
            print("Thanks for using SK Chatbot.")
            break
        else:
            # Construct the prompt using the current state of history
            prompt_history = "\n".join(
                f'User input: {interaction["User Input"]}\nAI response: {interaction["AI Response"]}' for interaction in history
            )

            prompt = f"""Instructions: You are a helpful assistant, that wil educate me about the Artificial Intelligence in a better way?
            If the query is out of the AI, don't guess; instead respond with "Sorry, I can just educate or assist you about AI".

            Remember: Also Greet the user, If user just give prompt such as:
                "Hi, Hello, Hey, and so on."
                you should say "Hello! How can I assist you today about AI?"

            {prompt_history}
            User Input: {request}
            Intent: """

            semantic_function = kernel.create_semantic_function(prompt)

            result = await semantic_function()
            print(f"AI Assistant: {result}")

            # Append the new interaction to history
            history.append({"User Input": request, "AI Response": result})
# now it has memory, it will remeber all the past conversation
            # lets demo
if __name__ == "__main__":
    asyncio.run(main())
