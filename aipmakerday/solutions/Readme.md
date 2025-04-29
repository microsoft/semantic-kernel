
The projects here demonstrate some approaches to create an agent using the suggested "Outdoor Activites Planner" agent.

- All projects results in the same functionality, only with different approaches
- Usage an agent follows the same pattern, regardless of agent-type or service-type.

### `ChatCompletion.Direct` (Recommended Approach)

Creates a `ChatCompletionAgent` based on OpenAI services through and endpoint an API key.

### `ChatCompletion.Inference`
Creates a `ChatCompletionAgent` based on Azure AI services (inference) through and endpoint an API key.

### `ChatCompletion.Connection`
Creates a `ChatCompletionAgent` based on OpenAI services discovered through a Foundry Project connection.

### `AzureAgent.Existing`
Creates an `AzureAIAgent` based on the identifier of an existing agent from a Foundry Project.

### `AzureAgent.New`
Creates an `AzureAIAgent` based on a new agent in a Foundry Project.
