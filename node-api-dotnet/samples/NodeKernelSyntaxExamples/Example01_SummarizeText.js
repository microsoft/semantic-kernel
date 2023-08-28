// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

// @ts-check

import './bin/Microsoft.SemanticKernel.Core.js';
import './bin/Microsoft.SemanticKernel.Connectors.AI.OpenAI.js';

import dotnet from 'node-api-dotnet';

const SK = dotnet.Microsoft.SemanticKernel;
const Logging = dotnet.Microsoft.Extensions.Logging;

// The JS marshaller does not yet support extension methods.
const kernelBuilder = SK.OpenAIKernelBuilderExtensions.WithAzureTextCompletionService(
  SK.Kernel.Builder,
  process.env['OPENAI_DEPLOYMENT'] || '',
  process.env['OPENAI_ENDPOINT'] || '',
  process.env['OPENAI_KEY'] || '',
);

const kernel = kernelBuilder
  .Build();

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

// The JS marshaller does not yet support extension methods.
const summarizeFunction = SK.InlineFunctionsDefinitionExtension
  .CreateSemanticFunction(kernel, skPrompt);

const summary = await kernel.RunAsync(textToSummarize, [ summarizeFunction ]);
console.log(summary.toString());
