# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai

kernel = sk.create_kernel()

# Load credentials from .env file
api_key, org_id = sk.openai_settings_from_dot_env()
# deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Configure LLM backend
kernel.config.add_text_backend(
    "davinci-003", sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id)
)
# kernel.config.add_text_backend(
#     "davinci-003", sk_oai.AzureTextCompletion(
#         "text-davinci-003", deployment_name, endpoint, api_key
#     )
# )

# Define semantic function using SK prompt template language
sk_prompt = """
{{$input}}

Give me the TLDR in 5 words.
"""

# Create the semantic function
tldr_function = kernel.create_semantic_function(
    sk_prompt, max_tokens=200, temperature=0, top_p=0.5
)

# User input
text_to_summarize = """
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
"""

print("Summarizing: ")
print(text_to_summarize)
print()

# Summarize and print
summary = asyncio.run(kernel.run_on_str_async(text_to_summarize, tldr_function))

output = str(summary).strip()
print(f"Summary is: '{output}'")
