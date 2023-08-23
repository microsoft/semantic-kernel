# Get Started with Semantic Kernel ⚡

Install the latest package:

    python -m pip install --upgrade semantic-kernel

# AI Services

## OpenAI / Azure OpenAI API keys

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy those keys into a `.env` file (see the `.env.example` file):

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

# Running a prompt

```python
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion, AzureTextCompletion

kernel = sk.Kernel()

# Prepare OpenAI service using credentials stored in the `.env` file
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id))

# Alternative using Azure:
# deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
# kernel.add_text_completion_service("dv", AzureTextCompletion(deployment, endpoint, api_key))

# Wrap your prompt in a function
prompt = kernel.create_semantic_function("""
1) A robot may not injure a human being or, through inaction,
allow a human being to come to harm.

2) A robot must obey orders given it by human beings except where
such orders would conflict with the First Law.

3) A robot must protect its own existence as long as such protection
does not conflict with the First or Second Law.

Give me the TLDR in exactly 5 words.""")

# Run your prompt
print(prompt()) # => Robots must not harm humans.
```

# **Semantic functions** are Prompts with input parameters

```python
# Create a reusable function with one input parameter
summarize = kernel.create_semantic_function("{{$input}}\n\nOne line TLDR with the fewest words.")

# Summarize the laws of thermodynamics
print(summarize("""
1st Law of Thermodynamics - Energy cannot be created or destroyed.
2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy."""))

# Summarize the laws of motion
print(summarize("""
1. An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.
2. The acceleration of an object depends on the mass of the object and the amount of force applied.
3. Whenever one object exerts a force on another object, the second object exerts an equal and opposite on the first."""))

# Summarize the law of universal gravitation
print(summarize("""
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

- [Getting started with Semantic Kernel](./notebooks/00-getting-started.ipynb)
- [Loading and configuring Semantic Kernel](./notebooks/01-basic-loading-the-kernel.ipynb)
- [Running AI prompts from file](./notebooks/02-running-prompts-from-file.ipynb)
- [Creating Semantic Functions at runtime (i.e. inline functions)](./notebooks/03-semantic-function-inline.ipynb)
- [Using Context Variables to Build a Chat Experience](./notebooks/04-context-variables-chat.ipynb)
- [Introduction to planners](./notebooks/05-using-the-planner.ipynb)
- [Building Memory with Embeddings](./notebooks/06-memory-and-embeddings.ipynb)
- [Using Hugging Face for Skills](./notebooks/07-hugging-face-for-skills.ipynb)
- [Combining native functions and semantic functions](./notebooks/08-native-function-inline.ipynb)
- [Groundedness Checking with Semantic Kernel](./notebooks/09-groundedness-checking.ipynb)
- [Returning multiple results per prompt](./notebooks/10-multiple-results-per-prompt.ipynb)
- [Streaming completions with Semantic Kernel](./notebooks/11-streaming-completions.ipynb)

# SK Frequently Asked Questions

## How does Python SK compare to the C# version of Semantic Kernel?

The two SDKs are compatible and at the core they follow the same design principles.
Some features are still available only in the C# version, and being ported
Refer to the [FEATURE MATRIX](../FEATURE_MATRIX.md) doc to see where
things stand in matching the features and functionality of the main SK branch.
Over time there will be some features available only in the Python version, and
others only in the C# version, for example adapters to external services,
scientific libraries, etc.
