# Using environment variables to setup Semantic Kernel

Semantic Kernel allows you multiple ways to setup your connectors. This guide shows that for OpenAI Connectors.

After installing the semantic-kernel package, you can try these out.

## From environment settings
using this method will try to find the required settings in the environment variables
this is done using pydantic settings, see the full docs of that here: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
We use a prefix for all the settings and then have names defined in the OpenAISettings class
for OpenAI that is OPENAI_ as the prefix, with the following settings:

- api_key (`OPENAI_API_KEY`): OpenAI API key, see https://platform.openai.com/account/api-keys
- org_id (`OPENAI_ORG_ID`): This is usually optional unless your account belongs to multiple organizations.
- chat_model_id (`OPENAI_CHAT_MODEL_ID`): The OpenAI chat model ID to use, for example, gpt-3.5-turbo or gpt-4,
  this variable is used in the OpenAIChatCompletion class and get's passed to the ai_model_id there.
- text_model_id (`OPENAI_TEXT_MODEL_ID`): The OpenAI text model ID to use, for example, gpt-3.5-turbo-instruct,
  this variable is used in the OpenAITextCompletion class and get's passed to the ai_model_id there.
- embedding_model_id (`OPENAI_EMBEDDING_MODEL_ID`): The embedding model ID to use, for example, text-embedding-ada-002,
  this variable is used in the OpenAITextEmbedding class and get's passed to the ai_model_id there.

```python
import os

from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

try:
    # when nothing is passed to the constructor,
    # it will use the above environment variable names to find the required settings,
    # in this case it will only fail if the OPENAI_CHAT_MODEL_ID and OPENAI_API_KEY are not found
    service = OpenAIChatCompletion(service_id="openai_chat_service")
except ValidationError as e:
    print(e)
```

## From a .env file
when you want to store and use your settings from a specific file (any file as long as it is in the .env format) you can pass the path to the file to the constructor this will still look at the same names of the settings as above, but will try to load them from the file

```python
try:
    # this will try to load the settings from the file at the given path
    service = OpenAIChatCompletion(service_id="openai_chat_service", env_file_path="path/to/env_file")
except ValidationError as e:
    print(e)
```

## From a different value
if you want to pass the settings yourself, you can do that by passing the values to the constructor this will ignore the environment variables and the .env file in this case our API_KEY is stored in a env variable called MY_API_KEY_VAR_NAME if using a file for this value, then we first need run the following code to load the .env file from the same folder as this file:

```python
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
```

After that pass the value directly to the constructor as shown below we can also fix another value, in this case the ai_model_id, which becomes chat_model_id in the settings, fixed to gpt-4o

```python
try:
    # this will use the given values as the settings
    api_key = os.getenv("MY_API_KEY_VAR_NAME")
    service = OpenAIChatCompletion(
        service_id="openai_chat_service",
        api_key=api_key,
        ai_model_id="gpt-4o",
    )
except ValidationError as e:
    print(e)
```

## One final note:

It is a convention that env settings are setup with all caps, and with underscores between words the loader that we use is case insensitive, so you can use any case you want in your env variables but it is a good practice to follow the convention and use all caps.
