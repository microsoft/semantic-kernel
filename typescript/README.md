# Get Started

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

kernel.config.addOpenAICompletionBackend('davinci-002', 'text-davinci-002', apiKey, orgId);

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
