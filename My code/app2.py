from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
import semantic_kernel as sk
import asyncio

import os
# from dotenv import load_dotenv
# load_dotenv('var.env')
# key = os.getenv('OPENAI_API_KEY')


key = os.environ["OPENAI_API_KEY"] = "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"


kernel = sk.Kernel()


kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))


# Wrap your prompt in a function
prompt1 = kernel.create_semantic_function("""
1) A robot may not injure a human being or, through inaction,
allow a human being to come to harm.

2) A robot must obey orders given it by human beings except where
such orders would conflict with the First Law.

3) A robot must protect its own existence as long as such protection
does not conflict with the First or Second Law.

Give me the TLDR in exactly 15 words.""")

# ---------------

prompt2 = kernel.create_semantic_function(
    "{{$input}}\n\nOne line TLDR with the 10 words.")

# OutPut Igot = Robots must prioritize human safety, obey orders, and protect themselves within ethical boundaries
# Run your prompt
# Note: functions are run asynchronously


# Output:
# > Energy conserved, entropy increases, zero entropy at 0K.
# > Objects move in response to forces.
# > Gravitational force between two point masses is inversely proportional to the square of the distance between them.


async def main():
    print(await prompt1())

    print(await prompt2("""
    1st Law of Thermodynamics - Energy cannot be created or destroyed.
    2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
    3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy."""))

    # Summarize the laws of motion
    print(await prompt2("""
    1. An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.
    2. The acceleration of an object depends on the mass of the object and the amount of force applied.
    3. Whenever one object exerts a force on another object, the second object exerts an equal and opposite on the first."""))

    # Summarize the law of universal gravitation
    print(await prompt2("""
    Every point mass attracts every single other point mass by a force acting along the line intersecting both points.
    The force is proportional to the product of the two masses and inversely proportional to the square of the distance between them."""))


if __name__ == "__main__":
    asyncio.run(main())


# Create a reusable function with one input parameter
