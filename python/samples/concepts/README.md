# Semantic Kernel Concepts by Feature

This section contains code snippets that demonstrate the usage of Semantic Kernel features.

| Features | Description |
| -------- | ----------- |
| AutoFunctionCalling | Using `Auto Function Calling` to allow function call capable models to invoke Kernel Functions automatically |
| ChatCompletion | Using [`ChatCompletion`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/chat_completion_client_base.py) messaging capable service with models  |
| Filtering | Creating and using Filters |
| Functions | Invoking [`Method`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_function_from_method.py) or [`Prompt`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_function_from_prompt.py) functions with [`Kernel`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/kernel.py) |
| Grounding | An example of how to perform LLM grounding |
| Logging | Showing how to set up logging |
| Memory | Using [`Memory`](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/SemanticKernel.Abstractions/Memory) AI concepts |
| On Your Data | Examples of using AzureOpenAI [`On Your Data`](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/use-your-data?tabs=mongo-db) |
| Planners | Showing the uses of [`Planners`](https://github.com/microsoft/semantic-kernel/tree/main/python/semantic_kernel/planners) |
| Plugins | Different ways of creating and using [`Plugins`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_plugin.py) |
| PromptTemplates | Using [`Templates`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/prompt_template/prompt_template_base.py) with parametrization for `Prompt` rendering  |
| RAG | Different ways of `RAG` (Retrieval-Augmented Generation) |
| Search | Using search services information |
| Service Selector | Shows how to create and use a custom service selector class. |
| Setup | How to setup environment variables for Semantic Kernel |
| TextGeneration | Using [`TextGeneration`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/text_completion_client_base.py) capable service with models  |

# Configuring the Kernel

In Semantic Kernel for Python, we leverage Pydantic Settings to manage configurations for AI and Memory Connectors, among other components. Here’s a clear guide on how to configure your settings effectively:

## Steps for Configuration

1. **Reading Environment Variables:**
   - **Primary Source:** Pydantic first attempts to read the required settings from environment variables.
   
2. **Using a .env File:**
   - **Fallback Source:** If the required environment variables are not set, Pydantic will look for a `.env` file in the current working directory.
   - **Custom Path (Optional):** You can specify an alternative path for the `.env` file via `env_file_path`. This can be either a relative or an absolute path.

3. **Direct Constructor Input:**
   - As an alternative to environment variables and `.env` files, you can pass the required settings directly through the constructor of the AI Connector or Memory Connector.

## Best Practices

- **.env File Placement:** We highly recommend placing the `.env` file in the `semantic-kernel/python` root directory. This is a common practice when developing in the Semantic Kernel repository.

By following these guidelines, you can ensure that your settings for various components are configured correctly, enabling seamless functionality and integration of Semantic Kernel in your Python projects.