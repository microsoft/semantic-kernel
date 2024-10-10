# Get Started with Semantic Kernel ⚡

Install the latest package:
```bash
python -m pip install --upgrade semantic-kernel
```
If you want to use some of the optional dependencies (OpenAI is installed by default), you can install them with:
```bash
python -m pip install --upgrade semantic-kernel[hugging_face]
```

or all of them:
```bash
python -m pip install --upgrade semantic-kernel[all]
```
# AI Services

## OpenAI / Azure OpenAI API keys

Make sure you have an
[OpenAI API Key](https://platform.openai.com) or
[Azure OpenAI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

There are two methods to manage keys, secrets, and endpoints:

1. Store them in environment variables. SK Python leverages pydantic settings to load keys, secrets, and endpoints. This means that there is a first attempt to load them from environment variables. The `.env` file naming applies to how the names should be stored as environment variables.

2. If you'd like to use the `.env` file, you will need to configure the `.env` file with the following keys in the file (see the `.env.example` file):

```bash
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=""
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME=""
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

You will then configure the Text/ChatCompletion class with the keyword argument `env_file_path`:

```python
chat_completion = OpenAIChatCompletion(service_id="test", env_file_path=<path_to_file>)
```

This optional `env_file_path` parameter will allow pydantic settings to use the `.env` file as a fallback to read the settings.

# Running a prompt

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

kernel = Kernel()

# Prepare OpenAI service using credentials stored in the `.env` file
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
api_key, org_id = sk.openai_settings_from_dot_env()
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
=======
api_key, org_id = sk.openai_settings_from_dot_env()
>>>>>>> Stashed changes
>>>>>>> origin/main
service_id="chat-gpt"
kernel.add_service(
    OpenAIChatCompletion(
        service_id=service_id,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
        ai_model_id="gpt-3.5-turbo",
        api_key=api_key,
        org_id=org_id
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        ai_model_id="gpt-3.5-turbo",
        api_key=api_key,
        org_id=org_id
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    )
)

# Alternative using Azure:
# kernel.add_service(
#   AzureChatCompletion(
#       service_id=service_id,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
# deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
# kernel.add_service(
#   AzureChatCompletion(
#       service_id="dv",
#       deployment_name=deployment,
#       base_url=endpoint,
#       api_key=api_key
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
#   )
# )

# Define the request settings
req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
req_settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
req_settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8

prompt = """
1) A robot may not injure a human being or, through inaction,
allow a human being to come to harm.

2) A robot must obey orders given it by human beings except where
such orders would conflict with the First Law.

3) A robot must protect its own existence as long as such protection
does not conflict with the First or Second Law.

Give me the TLDR in exactly 5 words."""

prompt_template_config = PromptTemplateConfig(
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
prompt_template_config = sk.PromptTemplateConfig(
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
prompt_template_config = sk.PromptTemplateConfig(
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    template=prompt,
    name="tldr",
    template_format="semantic-kernel",
    execution_settings=req_settings,
)

function = kernel.add_function(
    function_name="tldr_function",
    plugin_name="tldr_plugin",
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
function = kernel.create_function_from_prompt(
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
function = kernel.create_function_from_prompt(
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    prompt_template_config=prompt_template_config,
)

# Run your prompt
# Note: functions are run asynchronously
async def main():
    result = await kernel.invoke(function)
    print(result) # => Robots must not harm humans.

if __name__ == "__main__":
    asyncio.run(main())
# If running from a jupyter-notebook:
# await main()
```

# **Semantic Prompt Functions** are Prompts with input parameters

```python
# Create a reusable function summarize function
summarize = kernel.add_function(
    function_name="tldr_function",
    plugin_name="tldr_plugin",
    prompt="{{$input}}\n\nOne line TLDR with the fewest words.",
    prompt_template_settings=req_settings,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
summarize = kernel.create_function_from_prompt(
    template="{{$input}}\n\nOne line TLDR with the fewest words."
    execution_settings=req_settings,
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
summarize = kernel.create_function_from_prompt(
    template="{{$input}}\n\nOne line TLDR with the fewest words."
    execution_settings=req_settings,
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
)

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

The repository contains a few Python and C# notebooks that demonstrates how to
get started with the Semantic Kernel.

Python notebooks:

- [Getting started with Semantic Kernel](./samples/getting_started/00-getting-started.ipynb)
- [Loading and configuring Semantic Kernel](./samples/getting_started/01-basic-loading-the-kernel.ipynb)
- [Running AI prompts from file](./samples/getting_started/02-running-prompts-from-file.ipynb)
- [Creating Prompt Functions at runtime (i.e. inline functions)](./samples/getting_started/03-prompt-function-inline.ipynb)
- [Using Context Variables to Build a Chat Experience](./samples/getting_started/04-kernel-arguments-chat.ipynb)
- [Introduction to planners](./samples/getting_started/05-using-the-planner.ipynb)
- [Building Memory with Embeddings](./samples/getting_started/06-memory-and-embeddings.ipynb)
- [Using Hugging Face for Plugins](./samples/getting_started/07-hugging-face-for-plugins.ipynb)
- [Combining native functions and semantic functions](./samples/getting_started/08-native-function-inline.ipynb)
- [Groundedness Checking with Semantic Kernel](./samples/getting_started/09-groundedness-checking.ipynb)
- [Returning multiple results per prompt](./samples/getting_started/10-multiple-results-per-prompt.ipynb)
- [Streaming completions with Semantic Kernel](./samples/getting_started/11-streaming-completions.ipynb)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
- [Getting started with Semantic Kernel](./notebooks/00-getting-started.ipynb)
- [Loading and configuring Semantic Kernel](./notebooks/01-basic-loading-the-kernel.ipynb)
- [Running AI prompts from file](./notebooks/02-running-prompts-from-file.ipynb)
- [Creating Prompt Functions at runtime (i.e. inline functions)](./notebooks/03-prompt-function-inline.ipynb)
- [Using Context Variables to Build a Chat Experience](./notebooks/04-context-variables-chat.ipynb)
- [Introduction to planners](./notebooks/05-using-the-planner.ipynb)
- [Building Memory with Embeddings](./notebooks/06-memory-and-embeddings.ipynb)
- [Using Hugging Face for Plugins](./notebooks/07-hugging-face-for-plugins.ipynb)
- [Combining native functions and semantic functions](./notebooks/08-native-function-inline.ipynb)
- [Groundedness Checking with Semantic Kernel](./notebooks/09-groundedness-checking.ipynb)
- [Returning multiple results per prompt](./notebooks/10-multiple-results-per-prompt.ipynb)
- [Streaming completions with Semantic Kernel](./notebooks/11-streaming-completions.ipynb)
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

# SK Frequently Asked Questions

## How does Python SK compare to the C# version of Semantic Kernel?

The two SDKs are compatible and at the core they follow the same design principles.
Some features are still available only in the C# version, and being ported
Refer to the [FEATURE MATRIX](../FEATURE_MATRIX.md) doc to see where
things stand in matching the features and functionality of the main SK branch.
Over time there will be some features available only in the Python version, and
others only in the C# version, for example adapters to external services,
scientific libraries, etc.
# Quickstart with Poetry

## Installation

Install the Poetry package manager and create a project virtual environment.

```bash
# Install poetry package
pip3 install poetry
# Use poetry to install project deps
poetry install
# Use poetry to activate project venv
poetry shell
```

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy those keys into a `.env` file in this repo

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
```

### Quickstart ⚡

```python
import semantic_kernel as sk

kernel = sk.create_kernel()

api_key, org_id = sk.openai_settings_from_dot_env()

kernel.config.add_openai_completion_backend(
    "davinci-002", "text-davinci-002", api_key, org_id
)

sk_prompt = """
{{$input}}

Give me the TLDR in 5 words.
"""

text_to_summarize = """
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
"""

tldr_function = sk.extensions.create_semantic_function(
    kernel,
    sk_prompt,
    max_tokens=200,
    temperature=0,
    top_p=0.5,
)

summary = await kernel.run_on_str_async(text_to_summarize, tldr_function)
output = str(summary.variables).strip()
print("Output: " + output)

# Output: Protect humans, follow orders, survive.
```
