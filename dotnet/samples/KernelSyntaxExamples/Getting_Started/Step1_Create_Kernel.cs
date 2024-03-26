// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

/// <summary>
/// This example shows how to create and use a <see cref="Kernel"/>.
/// </summary>
public sealed class Step1_Create_Kernel : BaseTest
{
    /// <summary>
    /// Show how to create a <see cref="Kernel"/> and use it to execute prompts.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Example 1. Invoke the kernel with a prompt and display the result
        WriteLine(await kernel.InvokePromptAsync("What color is the sky?"));
        WriteLine();

        // Example 2. Invoke the kernel with a templated prompt and display the result
        KernelArguments arguments = new() { { "topic", "sea" } };
        WriteLine(await kernel.InvokePromptAsync("What color is the {{$topic}}?", arguments));
        WriteLine();

        // Example 3. Invoke the kernel with a templated prompt and stream the results to the display
        await foreach (var update in kernel.InvokePromptStreamingAsync("What color is the {{$topic}}? Provide a detailed explanation.", arguments))
        {
            Write(update);
        }

        WriteLine(string.Empty);

        // Example 4. Invoke the kernel with a templated prompt and execution settings
        arguments = new(new OpenAIPromptExecutionSettings { MaxTokens = 500, Temperature = 0.5 }) { { "topic", "dogs" } };
        WriteLine(await kernel.InvokePromptAsync("Tell me a story about {{$topic}}", arguments));

        // Example 5. Invoke the kernel with a templated prompt and execution settings configured to return JSON
#pragma warning disable SKEXP0010
        arguments = new(new OpenAIPromptExecutionSettings { ResponseFormat = "json_object" }) { { "topic", "chocolate" } };
        WriteLine(await kernel.InvokePromptAsync("Create a recipe for a {{$topic}} cake in JSON format", arguments));
    }

    public Step1_Create_Kernel(ITestOutputHelper output) : base(output)
    {
    }
}
