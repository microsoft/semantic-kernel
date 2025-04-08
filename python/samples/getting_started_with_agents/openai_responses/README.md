## Semantic Kernel OpenAI Responses Agent

The responses API is OpenAI's latest core API and an agentic API primitive. See more details [here](https://platform.openai.com/docs/guides/responses-vs-chat-completions).

### OpenAI Responses Agent

In Semantic Kernel, we don't currently support the Computer User Agent Tool. This is coming soon.

#### Environment Variables / Config

`OPENAI_RESPONSES_MODEL_ID=""`

### Azure Responses Agent

The Semantic Kernel Azure Responses Agent leverages Azure OpenAI's new stateful API. 
It brings together the best capabilities from the chat completions and assistants API in one unified experience.

Right now, there is no support with the `AzureResponsesAgent` for:

- Structured outputs
- tool_choice
- image_url pointing to an internet address
- The web search tool is also not supported, and is not part of the 2025-03-01-preview API.

#### API Support

`2025-03-01-preview` or later, therefore please use `AZURE_OPENAI_API_VERSION="2025-03-01-preview"`.

Please visit the following [link](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/responses?tabs=python-secure) to view region availability, model support, and further details.

#### Environment Variables / Config

`AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=""`

The other Azure OpenAI config values used for AzureAssistantAgent or AzureChatCompletion, like `AZURE_OPENAI_API_VERSION` or `AZURE_OPENAI_ENDPOINT` are still valid for the `AzureResponsesAgent`.