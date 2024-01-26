// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

#pragma warning disable CA5399

namespace Examples;

/// <summary>
/// To proceed with this example will be necessary to follow those steps:
/// 1. Install LMStudio Platform in your environment
/// 2. Open LM Studio
/// 3. Search and Download both Phi2 and Llama2 models (preferably the ones that uses 8GB RAM or more)
/// 4. Start the Rest API Server on http://localhost:1234
/// 5. Run the examples.
/// </summary>
public class Example77_LMStudio : BaseTest
{
    [Fact]
    public async Task Phi2ExampleAsync()
    {
        // Setup Phi-2 as the model in LM Studio UI.

        var kernel = Kernel.CreateBuilder()
            .AddLMStudioChatCompletion()
            .Build();

        string prompt = "Write a short poem about cats";
        var response = await kernel.InvokePromptAsync(prompt);

        this.WriteLine(response);
    }

    [Fact]
    public async Task Llama2ExampleAsync()
    {
        // Setup Llama2 as the model in LM Studio UI.

        var kernel = Kernel.CreateBuilder()
            .AddLMStudioChatCompletion()
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            MaxTokens = 1000,
        });

        var response = await kernel.InvokeAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." });
        this.WriteLine(response);
    }

    [Fact]
    public async Task Llama2StreamingExampleAsync()
    {
        // Setup Llama2 as the model in LM Studio UI.

        var kernel = Kernel.CreateBuilder()
            .AddLMStudioChatCompletion()
            .Build();

        var prompt = @"Rewrite the text between triple backticks into a business mail. Use a professional tone, be clear and concise.
                   Sign the mail as AI Assistant.

                   Text: ```{{$input}}```";

        var mailFunction = kernel.CreateFunctionFromPrompt(prompt, new OpenAIPromptExecutionSettings
        {
            Temperature = 0.7,
            MaxTokens = 1000,
        });

        await foreach (var word in kernel.InvokeStreamingAsync(mailFunction, new() { ["input"] = "Tell David that I'm going to finish the business plan by the end of the week." }))
        {
            this.WriteLine(word);
        };
    }

    [Fact]
    public async Task Phi2StreamingExampleAsync()
    {
        var kernel = Kernel.CreateBuilder()
            .AddLMStudioChatCompletion()
            .Build();

        string prompt = "Write a short poem about cats";

        await foreach (string word in kernel.InvokePromptStreamingAsync<string>(prompt))
        {
            this.Write(word);
        };
    }

    public Example77_LMStudio(ITestOutputHelper output) : base(output)
    {
    }

    public sealed class MyHttpMessageHandler : HttpClientHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            if (request.RequestUri != null && request.RequestUri.Host.Equals("api.openai.com", StringComparison.OrdinalIgnoreCase))
            {
                request.RequestUri = new Uri($"http://localhost:1234{request.RequestUri.PathAndQuery}");
            }

            return base.SendAsync(request, cancellationToken);
        }
    }
}

public static class KernelBuilderExtensions
{
    public static IKernelBuilder AddLMStudioChatCompletion(this IKernelBuilder builder)
    {
        var client = new HttpClient(new Example77_LMStudio.MyHttpMessageHandler());

        // LMStudio by default will ignore the local-api-key and local-model parameters.
        builder.AddOpenAIChatCompletion("local-model", "local-api-key", httpClient: client);
        return builder;
    }
}
