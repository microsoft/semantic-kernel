# Semantic Kernel for Python 🐍

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)

> **NOTE** This is an experimental Python implementation of the [Semantic Kernel (SK)](https://github.com/microsoft/semantic-kernel).

## Getting started

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

## How does this compare to the main C# repo?

Refer to the [FEATURE_PARITY.md](./FEATURE_PARITY.md) doc to see where things stand
in matching the features and functionality of the main SK repo.

## Why Python?

We believe that enabling Python is key to engaging with the great work being done
by the open source community in ML. From researchers writing state of the art ML
papers to app developers looking to quickly bring AI into their projects, we see
that the nexus of AI activity centers around Python due to the rich open source
ecosystem and tooling found in the language.

## Contributing and Community

We invite you to join us in developing the Semantic Kernel together! Please contribute
by using GitHub Discussions, opening GitHub Issues, sending us PRs.

## Code of Conduct

This project has adopted the
[Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the
[Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com)
with any additional questions or comments.

## License

Copyright (c) Microsoft Corporation. All rights reserved.

Licensed under the [MIT](LICENSE) license.
