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

public class Example77_LMStudio : BaseTest
{
    private sealed class MyHttpMessageHandler : HttpClientHandler
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

    [Fact]
    public async Task RunAsync()
    {
        // Setup Phi-2 as the model in LM Studio UI.

        using HttpClient client = new(new MyHttpMessageHandler());

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("fake-model-name", "fake-api-key", httpClient: client)
            .Build();

        string prompt = "Write a short poem about cats";
        var response = await kernel.InvokePromptAsync(prompt);

        this.WriteLine(response);
    }

    [Fact]
    public async Task Llama2ExampleAsync()
    {
        // Setup Llama2 as the model in LM Studio UI.

        using HttpClient client = new(new MyHttpMessageHandler());

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("fake-model-name", "fake-api-key", httpClient: client)
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

    public Example77_LMStudio(ITestOutputHelper output) : base(output)
    {
    }
}
