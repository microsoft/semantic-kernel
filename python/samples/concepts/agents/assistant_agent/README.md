## Azure Assistant Agents

Azure Assistant Agents are currently in preview and require a `-preview` API version (minimum version: `2024-05-01-preview`). As new features are introduced, API versions will be updated accordingly. For the latest versioning details, please refer to the [Azure OpenAI API preview lifecycle](/azure/ai-services/openai/api-version-deprecation).

To specify the correct API version, set the following environment variable (for example, in your `.env` file):

```bash
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
```

Alternatively, you can pass the `api_version` parameter when creating an `AzureAssistantAgent`:

```python
agent = await AzureAssistantAgent.create(
    name="<name>",
    instructions="<instructions>",
    api_version="2025-01-01-preview",
)
```