// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example shows a way of using OpenAI connector with other APIs that supports the same ChatCompletion Message API standard from OpenAI.
///
/// To proceed with this example will be necessary to follow those steps:
/// 1. Install LMStudio Platform in your environment
/// 2. Open LM Studio
/// 3. Search and Download both Phi2 and Llama2 models (preferably the ones that uses 8GB RAM or more)
/// 4. Start the Message API Server on http://localhost:1234
/// 5. Run the examples.
/// 6. Start the Ollama Message API Server on http://localhost:11434 using docker
/// 7. docker run -d --gpus=all -v "d:\temp\ollama:/root/.ollama" -p 11434:11434 --name ollama ollama/ollama <see href="https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image" />
/// 8. Set Llama2 as the current ollama model: docker exec -it ollama ollama run llama2
/// </summary>
public class Example78_CustomMessageAPIEndpoint : BaseTest
{
    [Theory]//(Skip = "Manual configuration needed")] //(Skip = "Manual configuration needed")]
    [InlineData("LMStudio", "http://localhost:1234", "llama2")] // Setup Llama2 as the model in LM Studio UI and start the Message API Server on http://localhost:1234
    [InlineData("Ollama", "http://localhost:11434", "llama2")] // Start the Ollama Message API Server on http://localhost:11434 using docker
    public async Task LocalModel_ExampleAsync(string messageAPIPlatform, string url, string modelId)
    {
        WriteLine($"Example using local {messageAPIPlatform}");
        // Setup Llama2 as the model in LM Studio UI.

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                endpoint: new Uri(url))
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            TopP = 0.5,
            MaxTokens = 1000,
        });

        var response = await kernel.InvokeAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." });
        this.WriteLine(response);
    }

    [Theory]//(Skip = "Manual configuration needed")] //(Skip = "Manual configuration needed")]
    [InlineData("LMStudio", "http://localhost:1234", "llama2")] // Setup Llama2 as the model in LM Studio UI and start the Message API Server on http://localhost:1234
    [InlineData("Ollama", "http://localhost:11434", "llama2")] // Start the Ollama Message API Server on http://localhost:11434 using docker
    public async Task LocalModel_StreamingExampleAsync(string messageAPIPlatform, string url, string modelId)
    {
        WriteLine($"Example using local {messageAPIPlatform}");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                endpoint: new Uri(url))
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            TopP = 0.5,
            MaxTokens = 1000,
        });

        await foreach (var word in kernel.InvokeStreamingAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." }))
        {
            this.WriteLine(word);
        };
    }

    public Example78_CustomMessageAPIEndpoint(ITestOutputHelper output) : base(output)
    {
    }
}
