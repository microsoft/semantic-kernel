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

# 3) Tell the AI what to do to avoid doing something wrong
# Often when an AI starts responding incorrectly, it's tempting to simply tell the AI to stop doing something. Unfortunately, this can often lead to the AI doing something even worse. For example, if you told the AI to stop returning back a hallucinated intent, it may start returning back an intent that is completely unrelated to the user's request.

# Instead, it's recommended that you tell the AI what it should do instead. For example, if you wanted to tell the AI to stop returning back a hallucinated intent, you might write the following prompt.


async def main():

    while (True):
        request = input("Your request: ")

        if request.upper() == "Exit":
            print("Thanks! for using SK Chatbot.")
            break
# To add examples, we can use few-shot prompting. With few-shot prompting, we provide the AI with a few examples of what we want it to do. For example, we could provide the following examples to help the AI distinguish between sending an email and sending an instant message.
        else:
            prompt = f"""Instructions: What is the intent of this request?
            If you don't know the intent, don't guess; instead respond with "Unknown".
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

            User Input: Can you send a very quick approval to the marketing team?
            Intent: SendMessage

            User Input: Can you send the full update to the marketing team?
            Intent: SendEmail
            
            User Input: {request}
            Intent: """

            semantic_function = kernel.create_semantic_function(prompt)

            result = await semantic_function()
            print(f"AI Assistant: {result}")

if __name__ == "__main__":
    asyncio.run(main())
