# Copyright (c) Microsoft. All rights reserved.

import os

from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

# Semantic Kernel allows you multiple ways to setup your connectors. This sample shows that for OpenAI Connectors.
# After installing the semantic-kernel package, you can use the following code to setup OpenAI Connector

# 1. From environment settings
# Using this method will try to find the required settings in the environment variables.
# This is done using pydantic settings, see the full docs of that here: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
# We use a prefix for all the settings and then have names defined in the OpenAISettings class.
# For OpenAI that is OPENAI_ as the prefix. For a full list of OpenAI settings, refer to:
# https://github.com/microsoft/semantic-kernel/blob/main/python/samples/concepts/setup/ALL_SETTINGS.md
try:
    # When nothing is passed to the constructor, it will use the above environment variable names
    # to find the required settings. In this case it will only fail if the OPENAI_CHAT_MODEL_ID and
    # OPENAI_API_KEY are not found
    service = OpenAIChatCompletion(service_id="openai_chat_service")
except ValidationError as e:
    print(e)

# 2. From a .env file
# When you want to store and use your settings from a specific file (any file as long as it is in the .env format),
# you can pass the path to the file to the constructor. This will still look at the same names of the settings as above,
# but will try to load them from the file
try:
    # This will try to load the settings from the file at the given path
    service = OpenAIChatCompletion(service_id="openai_chat_service", env_file_path="path/to/env_file")
except ValidationError as e:
    print(e)

# 3. From a different value
# If you want to pass the settings yourself, you can do that by passing the values to the constructor.
# This will ignore the environment variables and the .env file.
# In this case our API_KEY is stored in an env variable called MY_API_KEY_VAR_NAME.
# We can also hardcode another value, in this case the ai_model_id, which becomes chat_model_id in the
# settings, to gpt-4o
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

# One final note:
# It is a convention that env settings are setup with all caps, and with underscores between words
# the loader that we use is case insensitive, so you can use any case you want in your env variables
# but it is a good practice to follow the convention and use all caps.
