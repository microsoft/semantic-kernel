# Semantic Kernel

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)

> ℹ️ **NOTE**: The Python SDK for Semantic Kernel is currently in preview. While most
> of the features available in the C# SDK have been ported, there may be bugs and
> we're working on some features still - these will come into the repo soon. We are
> also actively working on improving the code quality and developer experience,
> and we appreciate your support, input and PRs!

> ℹ️ **NOTE**: This project is in early alpha and, just like AI, will evolve quickly.
> We invite you to join us in developing the Semantic Kernel together!
> Please contribute by
> using GitHub [Discussions](https://github.com/microsoft/semantic-kernel/discussions),
> opening GitHub [Issues](https://github.com/microsoft/semantic-kernel/issues/new/choose),
> sending us [PRs](https://github.com/microsoft/semantic-kernel/pulls).

**Semantic Kernel (SK)** is a lightweight SDK enabling integration of AI Large
Language Models (LLMs) with conventional programming languages. The SK extensible
programming model combines natural language **semantic functions**, traditional
code **native functions**, and **embeddings-based memory** unlocking new potential
and adding value to applications with AI.

SK supports
[prompt templating](docs/PROMPT_TEMPLATE_LANGUAGE.md), function
chaining,
[vectorized memory](docs/EMBEDDINGS.md), and
[intelligent planning](docs/PLANNER.md)
capabilities out of the box.

![image](https://user-images.githubusercontent.com/371009/221739773-cf43522f-c1e4-42f2-b73d-5ba84e21febb.png)

Semantic Kernel is designed to support and encapsulate several design patterns from the
latest in AI research, such that developers can infuse their applications with complex
[skills](docs/SKILLS.md) like [prompt](docs/PROMPT_TEMPLATE_LANGUAGE.md) chaining,
recursive reasoning, summarization, zero/few-shot learning, contextual memory,
long-term memory, [embeddings](docs/EMBEDDINGS.md), semantic indexing, [planning](docs/PLANNER.md),
and accessing external knowledge stores as well as your own data.

By joining the SK community, you can build AI-first apps faster and have a front-row
peek at how the SDK is being built. SK has been released as open-source so that more
pioneering developers can join us in crafting the future of this landmark moment
in the history of computing.

## Get Started with Semantic Kernel ⚡

Here is a quick example of how to use Semantic Kernel from a Python script.

1. Clone the repo and install SK dependencies, e.g. using `pip install -r python/requirements.txt`
2. Create a new Python file and add the code below.
3. Copy and paste your OpenAI **API key** in the script
   (support for Azure OpenAI is work in progress).
4. Using Python 3.8 or later, run the code. Enjoy!

```python
import sys
sys.path.append("./python")  # nopep8
import semantic_kernel as sk
import asyncio


kernel = sk.create_kernel()

kernel.config.add_openai_completion_backend(
    "davinci",
    "text-davinci-003",
    "...OpenAI Key...")

sk_prompt = """
{{$input}}

Give me the TLDR in 5 words.
"""

tldr_function = sk.extensions.create_semantic_function(
    kernel,
    sk_prompt,
    max_tokens=200,
    temperature=0,
    top_p=0.5)

text_to_summarize = """
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
"""

summary = asyncio.run(kernel.run_on_str_async(text_to_summarize, tldr_function))

print(f"Output: {summary}")

# Output: Robots must not harm humans.
```

## How does this compare to the main C# branch?

Refer to the [FEATURE_PARITY.md](python/FEATURE_PARITY.md) doc to see where
things stand in matching the features and functionality of the main SK branch.

## Contributing and Community

We welcome your contributions and suggestions to SK community! One of the easiest
ways to participate is to engage in discussions in the GitHub repository.
Bug reports and fixes are welcome!

For new features, components, or extensions, please open an issue and discuss with
us before sending a PR. This is to avoid rejection as we might be taking the core
in a different direction, but also to consider the impact on the larger ecosystem.

To learn more and get started:

-   Read the [documentation](https://aka.ms/sk/learn)
-   Learn how to [contribute](https://github.com/microsoft/semantic-kernel/blob/main/CONTRIBUTING.md) to the project
-   Join the [Discord community](https://aka.ms/SKDiscord)
-   Hear from the team on our [blog](https://aka.ms/sk/blog)

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
