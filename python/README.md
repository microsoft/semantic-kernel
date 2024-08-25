# Get Started with Semantic Kernel ⚡

### Install the Latest Package

```bash
python -m pip install --upgrade semantic-kernel
```

For optional dependencies (OpenAI is installed by default), use:

```bash
# For Hugging Face integration
python -m pip install --upgrade semantic-kernel[hugging_face]

# To install all optional dependencies
python -m pip install --upgrade semantic-kernel[all]
```

# AI Services

## OpenAI / Azure OpenAI API Keys

Make sure you have an [OpenAI API Key](https://platform.openai.com) or [Azure OpenAI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api).

### Managing Keys, Secrets, and Endpoints

You can manage your keys in two ways:

1. **Environment Variables**:  
   SK Python uses pydantic settings to load keys, secrets, and endpoints. The first attempt to load them will be from environment variables. Make sure to name them according to the `.env` file format.

2. **Using a `.env` File**:  
   Configure your `.env` file with the following keys (refer to the `.env.example`):

   ```bash
   OPENAI_API_KEY=""
   OPENAI_ORG_ID=""
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=""
   AZURE_OPENAI_TEXT_DEPLOYMENT_NAME=""
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=""
   AZURE_OPENAI_ENDPOINT=""
   AZURE_OPENAI_API_KEY=""
   ```

   Then, configure the `Text/ChatCompletion` class using the `env_file_path` keyword argument:

   ```python
   chat_completion = OpenAIChatCompletion(service_id="test", env_file_path=<path_to_file>)
   ```

   This optional `env_file_path` allows pydantic to use the `.env` file as a fallback for settings.

# Running a Prompt

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

kernel = Kernel()

# Prepare OpenAI service using credentials from the `.env` file
service_id = "chat-gpt"
kernel.add_service(
    OpenAIChatCompletion(service_id=service_id)
)

# Alternative using Azure:
# kernel.add_service(
#   AzureChatCompletion(service_id=service_id)
# )

# Define the request settings
req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8

prompt = """
1) A robot may not injure a human being or, through inaction, allow a human being to come to harm.
2) A robot must obey orders given it by human beings except where such orders would conflict with the First Law.
3) A robot must protect its own existence as long as such protection does not conflict with the First or Second Law.

Give me the TLDR in exactly 5 words.
"""

prompt_template_config = PromptTemplateConfig(
    template=prompt,
    name="tldr",
    template_format="semantic-kernel",
    execution_settings=req_settings,
)

function = kernel.add_function(
    function_name="tldr_function",
    plugin_name="tldr_plugin",
    prompt_template_config=prompt_template_config,
)

# Run the prompt asynchronously
async def main():
    result = await kernel.invoke(function)
    print(result)  # => Robots must not harm humans.

if __name__ == "__main__":
    asyncio.run(main())
# If running from a jupyter-notebook:
# await main()
```

# Semantic Prompt Functions: Prompts with Input Parameters

```python
# Create a reusable summarize function
summarize = kernel.add_function(
    function_name="tldr_function",
    plugin_name="tldr_plugin",
    prompt="{{$input}}\n\nOne line TLDR with the fewest words.",
    prompt_template_settings=req_settings,
)

# Examples of usage
# Summarize the laws of thermodynamics
print(await kernel.invoke(summarize, input="""
1st Law of Thermodynamics - Energy cannot be created or destroyed.
2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy."""))

# Summarize the laws of motion
print(await kernel.invoke(summarize, input="""
1. An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.
2. The acceleration of an object depends on the mass of the object and the amount of force applied.
3. Whenever one object exerts a force on another object, the second object exerts an equal and opposite on the first."""))

# Summarize the law of universal gravitation
print(await kernel.invoke(summarize, input="""
Every point mass attracts every single other point mass by a force acting along the line intersecting both points.
The force is proportional to the product of the two masses and inversely proportional to the square of the distance between them."""))

# Output:
# > Energy conserved, entropy increases, zero entropy at 0K.
# > Objects move in response to forces.
# > Gravitational force between two point masses is inversely proportional to the square of the distance between them.
```

# Semantic Kernel Notebooks

Explore more with the provided notebooks:

- [Getting started with Semantic Kernel](./samples/getting_started/00-getting-started.ipynb)
- [Loading and configuring Semantic Kernel](./samples/getting_started/01-basic-loading-the-kernel.ipynb)
- [Running AI prompts from file](./samples/getting_started/02-running-prompts-from-file.ipynb)
- [Creating Prompt Functions at runtime](./samples/getting_started/03-prompt-function-inline.ipynb)
- [Using Context Variables to Build a Chat Experience](./samples/getting_started/04-kernel-arguments-chat.ipynb)
- [Introduction to planners](./samples/getting_started/05-using-the-planner.ipynb)
- [Building Memory with Embeddings](./samples/getting_started/06-memory-and-embeddings.ipynb)
- [Using Hugging Face for Plugins](./samples/getting_started/07-hugging-face-for-plugins.ipynb)
- [Combining native functions and semantic functions](./samples/getting_started/08-native-function-inline.ipynb)
- [Groundedness Checking with Semantic Kernel](./samples/getting_started/09-groundedness-checking.ipynb)
- [Returning multiple results per prompt](./samples/getting_started/10-multiple-results-per-prompt.ipynb)
- [Streaming completions with Semantic Kernel](./samples/getting_started/11-streaming-completions.ipynb)

# SK Frequently Asked Questions

## How does Python SK compare to the C# version of Semantic Kernel?

Both SDKs are compatible and share core design principles. However, some features are still exclusive to the C# version and are being ported. For a detailed comparison, refer to the [FEATURE MATRIX](../FEATURE_MATRIX.md). In the future, some features may be unique to either the Python or C# versions.
