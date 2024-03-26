# SK Python Documentation Examples

This project contains a collection of examples used in documentation on [learn.microsoft.com](https://learn.microsoft.com/en-us/semantic-kernel/).

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.8 and above

## Configuring the sample

The samples can be configured with a `.env` file in the project which holds api keys and other secrets and configurations.

Make sure you have an
[Open AI API Key](https://openai.com/product/) or
[Azure Open AI service key](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

Copy the `.env.example` file to a new file named `.env`. Then, copy those keys into the `.env` file:

```
GLOBAL_LLM_SERVICE="OpenAI" # Toggle between "OpenAI" or "AzureOpenAI"

OPEN_AI__CHAT_COMPLETION_MODEL_ID="gpt-3.5-turbo-0125"
OPEN_AI__TEXT_COMPLETION_MODEL_ID="gpt-3.5-turbo-instruct"
OPENAI_API_KEY=""
OPENAI_ORG_ID=""

AZURE_OPEN_AI__CHAT_COMPLETION_DEPLOYMENT_NAME="gpt-35-turbo"
AZURE_OPEN_AI__TEXT_COMPLETION_DEPLOYMENT_NAME="text-davinci-003"
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_API_VERSION=""
```

_Note: if running the examples with VSCode, it will look for your .env file at the main root of the repository._

## Running the sample

To run the console application within Visual Studio Code, just hit `F5`.
Otherwise the sample can be run via the command line:

```
python.exe <absolute_path_to_sk_code>/python/samples/documentation_examples/planner.py
```
