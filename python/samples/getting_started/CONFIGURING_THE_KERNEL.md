## Configuring the Kernel

As covered in the notebooks, we require a `.env` file with the proper settings for the model you use. A `.env` file must be placed in the `getting_started` directory. Copy the contents of the `.env.example` file from this directory and paste it into the `.env` file that you just created.

If interested, as you learn more about Semantic Kernel, there are a few other ways to make sure your secrets, keys, and settings are used:

### 1. Environment Variables

Set the keys/secrets/endpoints as environment variables in your system. In Semantic Kernel, we leverage Pydantic Settings. If using Environment Variables, it isn't required to pass in explicit arguments to class constructors.

**NOTE: Please make sure to include `GLOBAL_LLM_SERVICE` set to either OpenAI, AzureOpenAI, or HuggingFace in your .env file or environment variables. If this setting is not included, the Service will default to AzureOpenAI.**

####  Option 1: using OpenAI

Add your [OpenAI Key](https://platform.openai.com/docs/overview) key to either your environment variables or to the `.env` file in the same folder (org Id only if you have multiple orgs):

```
GLOBAL_LLM_SERVICE="OpenAI"
OPENAI_API_KEY="sk-..."
OPENAI_ORG_ID=""
OPENAI_CHAT_MODEL_ID=""
```
The environment variables names should match the names used in the `.env` file, as shown above.

Use "keyword arguments" to instantiate an OpenAI Chat Completion service and add it to the kernel:

#### Option 2: using Azure OpenAI

Add your [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=programming-language-studio) settings to either your system's environment variables or to the `.env` file in the same folder:

```
GLOBAL_LLM_SERVICE="AzureOpenAI"
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://..."
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="..."
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME="..."
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="..."
AZURE_OPENAI_API_VERSION="..."
```
The environment variables names should match the names used in the `.env` file, as shown above.

Use "keyword arguments" to instantiate an Azure OpenAI Chat Completion service and add it to the kernel:

### 2. Custom .env file path

It is possible to configure the constructor with an absolute or relative file path to point the settings to a `.env` file located outside of the `getting_started` directory.

For OpenAI:

```
chat_completion = OpenAIChatCompletion(service_id="test", env_file_path='/path/to/file')
```

For AzureOpenAI:

```
chat_completion = AzureChatCompletion(service_id="test", env_file_path=env_file_path='/path/to/file')
```

### 3. Manual Configuration

- Manually configure the `api_key` or required parameters on either the `OpenAIChatCompletion` or `AzureChatCompletion` constructor with keyword arguments.
- This requires the user to manage their own keys/secrets as they aren't relying on the underlying environment variables or `.env` file.

### 4. Microsoft Entra Authentication

To learn how to use a Microsoft Entra Authentication token to authenticate to your Azure OpenAI resource, please navigate to the following [guide](../concepts/README.md#microsoft-entra-token-authentication).