import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


kernel = sk.Kernel()
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env

deployment, api_key, endpoint = azure_openai_settings_from_dot_env()

azure_text_service = AzureChatCompletion(deployment_name=deployment, endpoint=endpoint, api_key=api_key)    # set the deployment name to the value of your text model
kernel.add_chat_service("dv", azure_text_service)

prompt = """{{$input}}\n\nEXPLAIN THESE SYSTEM LOGS IN A HUMAN READABLE FORMAT."""
# prompt = "{{$input}}/n/nSummarize this"
log_explainer = kernel.create_semantic_function(prompt_template=prompt, max_tokens=2000, temperature=0.2, top_p=0.5)

for i in range(10):
    print(log_explainer(f"ERROR: {i}"))