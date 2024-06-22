// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace LocalModels;

/// <summary>
/// This example shows a way of using OpenAI connector with other APIs that supports the same ChatCompletion Message API standard from OpenAI.
///
/// To proceed with this example will be necessary to follow those steps:
/// 1. Install LMStudio Platform in your environment
/// 2. Open LM Studio
/// 3. Search and Download both Phi2 and Llama2 models (preferably the ones that uses 8GB RAM or more)
/// 4. Start the Message API Server on http://localhost:1234
/// 5. Run the examples.
///
/// OR
///
/// 1. Start the Ollama Message API Server on http://localhost:11434 using docker
/// 2. docker run -d --gpus=all -v "d:\temp\ollama:/root/.ollama" -p 11434:11434 --name ollama ollama/ollama <see href="https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image" />
/// 3. Set Llama2 as the current ollama model: docker exec -it ollama ollama run llama2
/// 4. Run the Ollama examples.
///
/// OR
///
/// 1. Start the LocalAI Message API Server on http://localhost:8080
/// 2. docker run -ti -p 8080:8080 localai/localai:v2.12.3-ffmpeg-core phi-2 <see href="https://localai.io/docs/getting-started/run-other-models/" />
/// 3. Run the LocalAI examples.
/// </summary>
public class MultipleProviders_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Theory(Skip = "Manual configuration needed")]
    [InlineData("LMStudio", "http://localhost:1234", "llama2")] // Setup Llama2 as the model in LM Studio UI and start the Message API Server on http://localhost:1234
    [InlineData("Ollama", "http://localhost:11434", "llama2")] // Start the Ollama Message API Server on http://localhost:11434 using docker
    [InlineData("LocalAI", "http://localhost:8080", "phi-2")]
    public async Task LocalModel_ExampleAsync(string messageAPIPlatform, string url, string modelId)
    {
        Console.WriteLine($"Example using local {messageAPIPlatform}");
        // Setup Llama2 as the model in LM Studio UI.

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                apiKey: null,
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
        Console.WriteLine(response);
    }

    [Theory(Skip = "Manual configuration needed")]
    [InlineData("LMStudio", "http://localhost:1234", "llama2")] // Setup Llama2 as the model in LM Studio UI and start the Message API Server on http://localhost:1234
    [InlineData("Ollama", "http://localhost:11434", "llama2")] // Start the Ollama Message API Server on http://localhost:11434 using docker
    [InlineData("LocalAI", "http://localhost:8080", "phi-2")]
    public async Task LocalModel_StreamingExampleAsync(string messageAPIPlatform, string url, string modelId)
    {
        Console.WriteLine($"Example using local {messageAPIPlatform}");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: modelId,
                apiKey: null,
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
            Console.WriteLine(word);
        }
    }
}
