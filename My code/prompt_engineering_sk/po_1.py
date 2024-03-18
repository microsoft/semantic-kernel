from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
import semantic_kernel as sk
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('var.env')
key = os.getenv('OPENAI_API_KEY')


kernel = sk.Kernel()

kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))

# prompt: I want to send an email to the marketing team celebrating their recent milestone.
# prompt: Can you send a very quick approval about ai team


async def main():

    while (True):
        request = input("Your request: ")

        if request.upper() == "Exit":
            print("Thanks! for using SK Chatbot.")
            break

        else:
            prompt = f"""Instructions: What is the intent of this request?
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.
            
            User Input: {request}
            Intent: """

            semantic_function = kernel.create_semantic_function(prompt)

            result = await semantic_function()
            print(f"AI Assistant: {result}")

if __name__ == "__main__":
    asyncio.run(main())
