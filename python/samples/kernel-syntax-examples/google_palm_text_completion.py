import semantic_kernel as sk
import asyncio
import google.generativeai as palm
import semantic_kernel.connectors.ai.google_palm.services.gp_text_completion as sk_gp
from semantic_kernel.utils.settings import google_palm_settings_from_dot_env
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings
)

async def text_completion_example(kernel, api_key):
    palm_text_completion = sk_gp.GooglePalmTextCompletion(
        "models/text-bison-001", api_key
    )
    kernel.add_text_completion_service("palm-2", palm_text_completion)
    settings = CompleteRequestSettings()
    user_mssg = "The opposite of hot is"
    answer = await palm_text_completion.complete_async(user_mssg, settings)

    
    
    return answer


async def main() -> None:
    
    kernel = sk.Kernel()
    apikey = google_palm_settings_from_dot_env()

    
   
    """
    palm.configure(api_key=apikey)
    response = palm.generate_text(prompt="The opposite of hot is")
    print(response.result)  # 'cold.'
    """
    

    response = await text_completion_example(kernel, apikey)
    print(response)
    
    
 
  
    
  

    return

if __name__ == "__main__":
    asyncio.run(main())
