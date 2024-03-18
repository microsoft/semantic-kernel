import asyncio
import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv

api_key = os.environ["OPENAI_API_KEY"] = "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"

kernel = sk.Kernel()

kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key))

async def main():
    Cooking_skill = kernel.import_semantic_plugin_from_directory("Plugins", "Cooking")
    recipe_function = Cooking_skill["recipe"]
    
    marketing_skill = kernel.import_semantic_plugin_from_directory("Plugins", "Marketing")
    advert_function = marketing_skill["AdvertisementGenerator"]
    
    # Use await to get the result from recipe_function
    recipe_result_context = await recipe_function("Chicken Adobo Filipino Style")
    recipe_result = recipe_result_context.result
    
    # Use await to get the result from advert_function
    advert_result_context = await advert_function(recipe_result)
    advert_result = advert_result_context.result
    
    print("Recipe: " + recipe_result)
    print(" ")
    print("Advert: " + advert_result)
    
asyncio.run(main())
