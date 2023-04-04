# Quickstart with Poetry

## Installation

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

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy those keys into a `.env` file in this repo (see the `.env.example` file):

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
```

### Quickstart ⚡

```python
import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai

kernel = sk.create_kernel()

# This requires a `.env` file in your current
# directory (see above)
api_key, org_id = sk.openai_settings_from_dot_env()

kernel.config.add_text_backend(
    "davinci-002", sk_oai.OpenAITextCompletion(
        "text-davinci-002", api_key, org_id
    )
)

sk_prompt = """
{{$input}}

Give me the TLDR in exactly 5 words.
"""

text_to_summarize = """
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
"""

tldr_function = kernel.create_semantic_function(
    sk_prompt,
    max_tokens=200,
    temperature=0,
    top_p=0.5,
)

summary = await kernel.run_on_str_async(text_to_summarize, tldr_function)
output = str(summary.variables).strip()
print("Output: " + output)

# Output: Robots must not harm humans.
```

Hint: if you want to run this via a file, say `my_sk_example.py`, you will
need to import `asyncio` and replace the `await kernel.run_on_str_async(...)`
call with `asyncio.run(kernel.run_on_str_async(...))`.

Hint: if you want to try this directly in your terminal, run `python3 -m asyncio`
and then paste the code above into the Python REPL. (This is to enable the
top-level `await` syntax.)
