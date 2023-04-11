# Setup

## OpenAI / Azure OpenAI API keys

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy those keys into a `.env` file (see the `.env.example` file):

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
```

## Using Poetry

First, navigate to the directory containing this README using your chosen shell.
You will need to have Python 3.10 installed.

Install the Poetry package manager and create a project virtual environment. (Note: we require at least Poetry 1.2.0 and Python 3.10.)

```bash
# Install poetry package
pip3 install poetry
# Use poetry to install project deps
poetry install
# Use poetry to activate project venv
poetry shell
```


# Get Started with Semantic Kernel ⚡

## Example: Running a simple prompt.

```python
import semantic_kernel as sk
from semantic_kernel.ai.open_ai import OpenAITextCompletion

kernel = sk.create_kernel()

# Prepare OpenAI backend using credentials stored in the `.env` file
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.config.add_text_backend("dv", OpenAITextCompletion("text-davinci-003", api_key, org_id))

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

## Example: Turn prompts into **reusable functions** with input parameters.

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
# Energy conserved, entropy increases, zero entropy at 0K.
# Objects move in response to forces.
# Gravitational force between two point masses is inversely proportional to the square of the distance between them.
```

## How does this compare to the C# version of Semantic Kernel?

Refer to the [FEATURE_PARITY.md](FEATURE_PARITY.md) doc to see where
things stand in matching the features and functionality of the main SK branch.