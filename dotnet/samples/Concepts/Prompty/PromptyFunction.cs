// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Prompty;

public class PromptyFunction(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task InlineFunctionAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        string promptTemplate = @"---
name: Contoso_Chat_Prompt
description: A sample prompt that responds with what Seattle is.
authors:
  - ????
model:
  api: chat
  configuration:
    type: openai
---
system:
You are a helpful assistant who knows all about cities in the USA

user:
What is Seattle?
";

        var function = kernel.CreateFunctionFromPrompty(promptTemplate);

        var result = await kernel.InvokeAsync(function);
        Console.WriteLine(result);
    }
}
