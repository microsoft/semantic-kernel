from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
import semantic_kernel as sk
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('var.env')
key = os.getenv('OPENAI_API_KEY')


kernel = sk.Kernel()

# Prepare OpenAI service using credentials stored in the `.env` file
# api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))


summarize = kernel.create_semantic_function(
    "{{$input}}\n\nOne line TLDR with the fewest words.")


async def main():
    # Summarize the laws of thermodynamics
    print(await summarize("""
    1st Law of Thermodynamics - Energy cannot be created or destroyed.
    2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
    3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy."""))

    # Summarize the laws of motion
    print(await summarize("""
    1. An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.
    2. The acceleration of an object depends on the mass of the object and the amount of force applied.
    3. Whenever one object exerts a force on another object, the second object exerts an equal and opposite on the first."""))

    # Summarize the law of universal gravitation
    print(await summarize("""
    Every point mass attracts every single other point mass by a force acting along the line intersecting both points.
    The force is proportional to the product of the two masses and inversely proportional to the square of the distance between them."""))


if __name__ == "__main__":
    asyncio.run(main())


# Create a reusable function with one input parameter
