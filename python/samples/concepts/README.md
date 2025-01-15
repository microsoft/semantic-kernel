# Semantic Kernel Concepts by Feature

## Table of Contents

### Agents - Creating and using [agents](../../semantic_kernel/agents/) in Semantic Kernel

- [Assistant Agent Chart Maker](./agents/assistant_agent_chart_maker.py)
- [Assistant Agent File Manipulation](./agents/assistant_agent_file_manipulation.py)
- [Assistant Agent File Manipulation Streaming](./agents/assistant_agent_file_manipulation_streaming.py)
- [Assistant Agent Retrieval](./agents/assistant_agent_retrieval.py)
- [Assistant Agent Streaming](./agents/assistant_agent_streaming.py)
- [Chat Completion Function Termination](./agents/chat_completion_function_termination.py)
- [Mixed Chat Agents](./agents/mixed_chat_agents.py)
- [Mixed Chat Agents Plugins](./agents/mixed_chat_agents_plugins.py)
- [Mixed Chat Files](./agents/mixed_chat_files.py)
- [Mixed Chat Reset](./agents/mixed_chat_reset.py)
- [Mixed Chat Streaming](./agents/mixed_chat_streaming.py)

### Audio - Using services that support audio-to-text and text-to-audio conversion

- [Chat with Audio Input](./audio/01-chat_with_audio_input.py)
- [Chat with Audio Output](./audio/02-chat_with_audio_output.py)
- [Chat with Audio Input and Output](./audio/03-chat_with_audio_input_output.py)
- [Audio Player](./audio/audio_player.py)
- [Audio Recorder](./audio/audio_recorder.py)

### AutoFunctionCalling - Using `Auto Function Calling` to allow function call capable models to invoke Kernel Functions automatically

- [Azure Python Code Interpreter Function Calling](./auto_function_calling/azure_python_code_interpreter_function_calling.py)
- [Function Calling with Required Type](./auto_function_calling/function_calling_with_required_type.py)
- [Parallel Function Calling](./auto_function_calling/parallel_function_calling.py)
- [Chat Completion with Auto Function Calling Streaming](./auto_function_calling/chat_completion_with_auto_function_calling_streaming.py)
- [Functions Defined in JSON Prompt](./auto_function_calling/functions_defined_in_json_prompt.py)
- [Chat Completion with Manual Function Calling Streaming](./auto_function_calling/chat_completion_with_manual_function_calling_streaming.py)
- [Functions Defined in YAML Prompt](./auto_function_calling/functions_defined_in_yaml_prompt.py)
- [Chat Completion with Auto Function Calling](./auto_function_calling/chat_completion_with_auto_function_calling.py)
- [Chat Completion with Manual Function Calling](./auto_function_calling/chat_completion_with_manual_function_calling.py)
- [Nexus Raven](./auto_function_calling/nexus_raven.py)

### ChatCompletion - Using [`ChatCompletion`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/chat_completion_client_base.py) messaging capable service with models

- [Simple Chatbot](./chat_completion/simple_chatbot.py)
- [Simple Chatbot Kernel Function](./chat_completion/simple_chatbot_kernel_function.py)
- [Simple Chatbot Logit Bias](./chat_completion/simple_chatbot_logit_bias.py)
- [Simple Chatbot Store Metadata](./chat_completion/simple_chatbot_store_metadata.py)
- [Simple Chatbot Streaming](./chat_completion/simple_chatbot_streaming.py)
- [Simple Chatbot with Image](./chat_completion/simple_chatbot_with_image.py)

### ChatHistory - Using and serializing the [`ChatHistory`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/contents/chat_history.py)

- [Serialize Chat History](./chat_history/serialize_chat_history.py)

### Filtering - Creating and using Filters

- [Auto Function Invoke Filters](./filtering/auto_function_invoke_filters.py)
- [Function Invocation Filters](./filtering/function_invocation_filters.py)
- [Function Invocation Filters Stream](./filtering/function_invocation_filters_stream.py)
- [Prompt Filters](./filtering/prompt_filters.py)
- [Retry with Filters](./filtering/retry_with_filters.py)

### Functions - Invoking [`Method`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_function_from_method.py) or [`Prompt`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_function_from_prompt.py) functions with [`Kernel`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/kernel.py)

- [Kernel Arguments](./functions/kernel_arguments.py)

### Grounding - An example of how to perform LLM grounding

- [Grounded](./grounding/grounded.py)

### Local Models - Using the [`OpenAI connector`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/open_ai/services/open_ai_chat_completion.py) and [`OnnxGenAI connector`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/onnx/services/onnx_gen_ai_chat_completion.py) to talk to models hosted locally in Ollama, OnnxGenAI, and LM Studio

- [ONNX Chat Completion](./local_models/onnx_chat_completion.py)
- [LM Studio Text Embedding](./local_models/lm_studio_text_embedding.py)
- [LM Studio Chat Completion](./local_models/lm_studio_chat_completion.py)
- [ONNX Phi3 Vision Completion](./local_models/onnx_phi3_vision_completion.py)
- [Ollama Chat Completion](./local_models/ollama_chat_completion.py)
- [ONNX Text Completion](./local_models/onnx_text_completion.py)

### Logging - Showing how to set up logging

- [Setup Logging](./logging/setup_logging.py)

### Memory - Using [`Memory`](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/SemanticKernel.Abstractions/Memory) AI concepts

- [Azure Cognitive Search Memory](./memory/azure_cognitive_search_memory.py)
- [Memory Data Models](./memory/data_models.py)
- [New Memory](./memory/new_memory.py)
- [Pandas Memory](./memory/pandas_memory.py)

### Model-as-a-Service - Using models deployed as [`serverless APIs on Azure AI Studio`](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/deploy-models-serverless?tabs=azure-ai-studio) to benchmark model performance against open-source datasets

- [MMLU Model Evaluation](./model_as_a_service/mmlu_model_eval.py)

### On Your Data - Examples of using AzureOpenAI [`On Your Data`](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/use-your-data?tabs=mongo-db)

- [Azure Chat GPT with Data API](./on_your_data/azure_chat_gpt_with_data_api.py)
- [Azure Chat GPT with Data API Function Calling](./on_your_data/azure_chat_gpt_with_data_api_function_calling.py)
- [Azure Chat GPT with Data API Vector Search](./on_your_data/azure_chat_gpt_with_data_api_vector_search.py)

### Planners - Showing the uses of [`Planners`](https://github.com/microsoft/semantic-kernel/tree/main/python/semantic_kernel/planners)

- [Sequential Planner](./planners/sequential_planner.py)
- [OpenAI Function Calling Stepwise Planner](./planners/openai_function_calling_stepwise_planner.py)
- [Azure OpenAI Function Calling Stepwise Planner](./planners/azure_openai_function_calling_stepwise_planner.py)

### Plugins - Different ways of creating and using [`Plugins`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/functions/kernel_plugin.py)

- [Azure Key Vault Settings](./plugins/azure_key_vault_settings.py)
- [Azure Python Code Interpreter](./plugins/azure_python_code_interpreter.py)
- [OpenAI Function Calling with Custom Plugin](./plugins/openai_function_calling_with_custom_plugin.py)
- [Plugins from Directory](./plugins/plugins_from_dir.py)

### Processes - Examples of using the [`Process Framework`](../../semantic_kernel/processes/)

- [Cycles with Fan-In](./processes/cycles_with_fan_in.py)
- [Nested Process](./processes/nested_process.py)

### PromptTemplates - Using [`Templates`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/prompt_template/prompt_template_base.py) with parametrization for `Prompt` rendering

- [Template Language](./prompt_templates/template_language.py)
- [Azure Chat GPT API Jinja2](./prompt_templates/azure_chat_gpt_api_jinja2.py)
- [Load YAML Prompt](./prompt_templates/load_yaml_prompt.py)
- [Azure Chat GPT API Handlebars](./prompt_templates/azure_chat_gpt_api_handlebars.py)
- [Configuring Prompts](./prompt_templates/configuring_prompts.py)

### RAG - Different ways of `RAG` (Retrieval-Augmented Generation)

- [RAG with Text Memory Plugin](./rag/rag_with_text_memory_plugin.py)
- [Self-Critique RAG](./rag/self-critique_rag.py)

### Reasoning - Using [`ChatCompletion`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/chat_completion_client_base.py) to reason with OpenAI Reasoning

- [Simple Chatbot](./reasoning/simple_reasoning.py)
- [Simple Function Calling](./reasoning/simple_reasoning_function_calling.py)

### Search - Using [`Search`](https://github.com/microsoft/semantic-kernel/tree/main/python/semantic_kernel/connectors/search) services information

- [Bing Search Plugin](./search/bing_search_plugin.py)
- [Bing Text Search](./search/bing_text_search.py)
- [Bing Text Search as Plugin](./search/bing_text_search_as_plugin.py)
- [Google Search Plugin](./search/google_search_plugin.py)
- [Google Text Search as Plugin](./search/google_text_search_as_plugin.py)

### Service Selector - Shows how to create and use a custom service selector class

- [Custom Service Selector](./service_selector/custom_service_selector.py)

### Setup - How to set up environment variables for Semantic Kernel

- [OpenAI Environment Setup](./setup/openai_env_setup.py)
- [Chat Completion Services](./setup/chat_completion_services.py)

### Structured Outputs - How to leverage OpenAI's json_schema [`Structured Outputs`](https://platform.openai.com/docs/guides/structured-outputs) functionality

- [JSON Structured Outputs](./structured_outputs/json_structured_outputs.py)
- [JSON Structured Outputs Function Calling](./structured_outputs/json_structured_outputs_function_calling.py)

### TextGeneration - Using [`TextGeneration`](https://github.com/microsoft/semantic-kernel/blob/main/python/semantic_kernel/connectors/ai/text_completion_client_base.py) capable service with models

- [Text Completion Client](./local_models/onnx_text_completion.py)

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

## Microsoft Entra Token Authentication

To authenticate to your Azure resources using a Microsoft Entra Authentication Token, the `AzureChatCompletion` AI Service connector now supports this as a built-in feature. If you do not provide an API key -- either through an environment variable, a `.env` file, or the constructor -- and you also do not provide a custom `AsyncAzureOpenAI` client, an `ad_token`, or an `ad_token_provider`, the `AzureChatCompletion` connector will attempt to retrieve a token using the [`DefaultAzureCredential`](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python).

To successfully retrieve and use the Entra Auth Token, you need the `Cognitive Services OpenAI Contributor` role assigned to your Azure OpenAI resource. By default, the `https://cognitiveservices.azure.com` token endpoint is used. You can override this endpoint by setting an environment variable `.env` variable as `AZURE_OPENAI_TOKEN_ENDPOINT` or by passing a new value to the `AzureChatCompletion` constructor as part of the `AzureOpenAISettings`.

## Best Practices

- **.env File Placement:** We highly recommend placing the `.env` file in the `semantic-kernel/python` root directory. This is a common practice when developing in the Semantic Kernel repository.

By following these guidelines, you can ensure that your settings for various components are configured correctly, enabling seamless functionality and integration of Semantic Kernel in your Python projects.