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

# Hardware Acceleration Support

## Intel Gaudi HPU Support

Semantic Kernel now supports Intel Gaudi HPUs for accelerated AI workloads. Gaudi HPUs (Habana Processing Units) are specialized AI accelerators designed by Habana Labs (an Intel company) that offer high-performance, cost-effective training and inference for deep learning models.

### Key Benefits

- **Cost-Effective Performance**: Gaudi HPUs can provide significant cost savings compared to other accelerators for certain AI workloads
- **Optimized for Transformers**: Specially designed for transformer-based models like those used in LLMs
- **Seamless Integration**: Works with popular frameworks like PyTorch and Hugging Face Transformers
- **AWS DL1 and DL2 Support**: Fully compatible with AWS DL1 and DL2 instances

### Installation for Gaudi HPU instances on AWS

If you're using Semantic Kernel on AWS Gaudi HPU instances that already have PyTorch pre-installed (version 2.4.0a0+git74cd574), you can use the following methods to install Semantic Kernel without reinstalling PyTorch:

#### Using the provided script

```bash
# Clone the repository
git clone https://github.com/microsoft/semantic-kernel.git
cd semantic-kernel

# Run the Gaudi installation script
./install_for_gaudi.sh
```

#### Using Make

```bash
# Clone the repository
git clone https://github.com/microsoft/semantic-kernel.git
cd semantic-kernel/python

make install-uv
# Install for Gaudi (skips PyTorch installation)
make install-gaudi
```

### Using Semantic Kernel with Gaudi HPUs

To use Semantic Kernel with Gaudi HPUs, all you need to do is add the `use_hpu=True` flag to the Hugging Face text embedding service.

```python
embedding_service = HuggingFaceTextEmbedding(ai_model_id="sentence-transformers/all-MiniLM-L6-v2", use_hpu=True)
```

### Performance Tuning for Gaudi

For optimal performance on Gaudi HPUs:

1. Use the `optimum-habana` package (automatically installed with the `gaudi` extras)
2. Set appropriate batch sizes based on your model and available memory
3. Enable mixed precision (FP16/BF16) for faster computation
4. Consider using Habana-optimized models when available

For more information about Intel Gaudi HPUs, visit the [Habana Labs documentation](https://docs.habana.ai/).

# AI Services

## OpenAI / Azure OpenAI API keys

Make sure you have an
[OpenAI API Key](https://platform.openai.com/) or
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

Put the .env file in the root directory.

If you place the .env in a different directory, configure the Text/ChatCompletion class with the keyword argument `env_file_path`:

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
service_id="chat-gpt"
kernel.add_service(
    OpenAIChatCompletion(
        service_id=service_id,
    )
)

# Alternative using Azure:
# kernel.add_service(
#   AzureChatCompletion(
#       service_id=service_id,
#   )
# )

# Define the request settings
req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
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
    prompt_execution_settings=req_settings,
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

# SK Frequently Asked Questions

## How does Python SK compare to the C# version of Semantic Kernel?

The two SDKs are compatible and at the core they follow the same design principles.
Some features are still available only in the C# version, and being ported
Refer to the [FEATURE MATRIX](../FEATURE_MATRIX.md) doc to see where
things stand in matching the features and functionality of the main SK branch.
Over time there will be some features available only in the Python version, and
others only in the C# version, for example adapters to external services,
scientific libraries, etc.

# Configuration System

This directory contains a configuration system for the application. The system provides a clean, type-safe way to manage configuration options, while maintaining backward compatibility with the existing argparse-based approach.

## Files

- `config.py`: Contains the `Config` dataclass that defines all configuration options
- `config_utils.py`: Provides utility functions to convert between the Config class and argparse
- `test.py`: The main application file, updated to use the Config class