from dotenv import dotenv_values
from promptflow import PFClient
from promptflow.entities import AzureOpenAIConnection

pf_client = PFClient()

# Run a single test of a flow
#################################################

# Load the configuration from the .env file
config = dotenv_values(".env")
deployment_type = config.get("AZURE_OPEN_AI__DEPLOYMENT_TYPE", None)
if deployment_type == "chat-completion":
    deployment_name = config.get("AZURE_OPEN_AI__CHAT_COMPLETION_DEPLOYMENT_NAME", None)
elif deployment_type == "text-completion":
    deployment_name = config.get("AZURE_OPEN_AI__TEXT_COMPLETION_DEPLOYMENT_NAME", None)

# Define the inputs of the flow
inputs = {
    "text": "What is 2 plus 3?",
    "deployment_type": deployment_type,
    "deployment_name": deployment_name,
}

# Initialize an AzureOpenAIConnection object
connection = AzureOpenAIConnection(
    name="AzureOpenAIConnection",
    type="Custom",
    api_key=config.get("AZURE_OPEN_AI__API_KEY", None),
    api_base=config.get("AZURE_OPEN_AI__ENDPOINT", None),
    api_version="2023-03-15-preview",
)

# Add connections to the Prompt flow client
pf_client.connections.create_or_update(connection)

# Run the flow
flow_result = pf_client.test(flow="perform_math", inputs=inputs)

# Print the outputs of the flow
print(f"Flow outputs: {flow_result}")
