// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

// This example shows how to create and use a <see cref="Kernel"/>.
public class Step1_Create_Kernel : BaseTest
{
    public Step1_Create_Kernel(ITestOutputHelper output) : base(output)
    {
    }

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
        this._output.WriteLine(await kernel.InvokePromptAsync("What color is the sky?"));
        this._output.WriteLine();

        // Example 2. Invoke the kernel with a templated prompt and display the result
        KernelArguments arguments = new() { { "topic", "sea" } };
        this._output.WriteLine(await kernel.InvokePromptAsync("What color is the {{$topic}}?", arguments));
        this._output.WriteLine();

        // Example 3. Invoke the kernel with a templated prompt and stream the results to the display

        await foreach (var update in kernel.InvokePromptStreamingAsync("What color is the {{$topic}}? Provide a detailed explanation.", arguments))
        {
            this._output.Write(update);
            // Console.Write(update);
        }

        this._output.WriteLine(string.Empty);

        // Example 4. Invoke the kernel with a templated prompt and execution settings
        arguments = new(new OpenAIPromptExecutionSettings { MaxTokens = 500, Temperature = 0.5 }) { { "topic", "dogs" } };
        this._output.WriteLine(await kernel.InvokePromptAsync("Tell me a story about {{$topic}}", arguments));
    }
}
