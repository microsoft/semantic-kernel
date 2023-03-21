# Semantic Kernel

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)

> ℹ️ **NOTE**: The TypeScript SDK for Semantic Kernel is currently experimental. While
> part of the features available in the C# SDK have been ported, there may be bugs and
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

## Installation

Install the Yarn package manager and create a project virtual environment.

```bash
# Install yarn package
npm install -g yarn
# Use Yarn to install project deps
yarn install
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

```typescript
import { SemanticKernel as sk } from 'semantic-kernel';

const kernel = sk.createKernel();
const [apiKey, orgId] = sk.openaiSettingsFromDotEnv();

kernel.config.addOpenAICompletionBackend('davinci-003', 'text-davinci-003', apiKey, orgId);

const skPrompt = `
{{$input}}

Give me the TLDR in 5 words.
`;

const textToSummarize = `
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
`;

const tldrFunction = sk.extensions.createSemanticFunction({
  kernel,
  skPrompt,
  maxTokens: 200,
  temperature: 0,
  topP: 0.5,
});

const summary = await kernel.runOnStrAsync(textToSummarize, tldrFunction);
const output = summary?.variables?.trim();
console.log(`Output: ${output}`);

// Output: Protect humans, follow orders, survive.
```

## How does this compare to the main C# branch?

This branch is an experimental port of SK to TypeScript, very much work in progress.
Please do not take dependency on this branch, and consider it only for experimental purposes.

If you would like having a complete TypeScript port of Semantic Kernel, please let us know!

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
