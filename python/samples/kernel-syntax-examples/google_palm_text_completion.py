import semantic_kernel as sk
import asyncio
import google.generativeai as palm
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.utils.settings import google_palm_settings_from_dot_env

async def chat_request_example(kernel, api_key, org_id):
    pass


async def main() -> None:
    kernel = sk.Kernel()
    apikey = google_palm_settings_from_dot_env()
    """
    os.environ['GOOGLE_API_KEY'] = ""
    apikey = os.environ.get('GOOGLE_API_KEY')
    """
 
    palm.configure(api_key=apikey)
    response = palm.generate_text(prompt="The opposite of hot is")
    print(response.result)  # 'cold.'

    
  

    return

if __name__ == "__main__":
    asyncio.run(main())
