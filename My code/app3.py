from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
import semantic_kernel as sk
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('var.env')
key = os.getenv('OPENAI_API_KEY')

kernel = sk.Kernel()

prompt = """{{$history}}
User: {{$request}}
Assistant:  """

history = []

kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))


async def main():
    while True:
        request = input("User > ")

        variables = sk.ContextVariables()
        variables["request"] = request
        variables["history"] = "\n".join(history)

        # Run the prompt
        semantic_function = kernel.create_semantic_function(request)
        result = await semantic_function()

        # Add the request to the history
        history.append("User: " + request)
        history.append("Assistant" + result.result)

        print(f"Assistant > {result}")

if __name__ == "__main__":
    asyncio.run(main())
