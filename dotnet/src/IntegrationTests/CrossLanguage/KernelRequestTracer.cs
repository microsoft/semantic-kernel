// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

internal sealed class KernelRequestTracer : IDisposable
{
    private const string DummyResponse = @"{
    ""id"": ""chatcmpl-abc123"",
    ""object"": ""chat.completion"",
    ""created"": 1677858242,
    ""model"": ""gpt-3.5-turbo-0613"",
    ""usage"": {
        ""prompt_tokens"": 13,
        ""completion_tokens"": 7,
        ""total_tokens"": 20
    },
    ""choices"": [
        {
            ""message"": {
                ""role"": ""assistant"",
                ""content"": ""\n\nThis is a test!""
            },
            ""logprobs"": null,
            ""finish_reason"": ""stop"",
            ""index"": 0
        }
    ]
   }";

    private HttpClient? _httpClient;
    private HttpMessageHandlerStub? _httpMessageHandlerStub;

    public Kernel GetNewKernel()
    {
        this.ResetHttpComponents();

        return Kernel.CreateBuilder()
                     .AddOpenAIChatCompletion(
                        modelId: "Dummy",
                        apiKey: "Not used in this test",
                        httpClient: this._httpClient)
                     .Build();
    }

    public string GetRequestContent()
    {
        return System.Text.Encoding.UTF8.GetString(this._httpMessageHandlerStub?.RequestContent ?? Array.Empty<byte>());
    }

    public static async Task InvokePromptStreamingAsync(Kernel kernel, string prompt, KernelArguments? args = null)
    {
        try
        {
            await foreach (var update in kernel.InvokePromptStreamingAsync<ChatMessageContent>(prompt, arguments: args))
            {
                // Do nothing with received response
            }
        }
        catch (NotSupportedException)
        {
            // Ignore this exception
        }
    }

    private void ResetHttpComponents()
    {
        this.DisposeHttpResources();

        this._httpMessageHandlerStub = new HttpMessageHandlerStub();
        this._httpMessageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(DummyResponse,
                                        Encoding.UTF8, "application/json")
        };
        this._httpClient = new HttpClient(this._httpMessageHandlerStub);
    }

    public void Dispose()
    {
        this.DisposeHttpResources();
        GC.SuppressFinalize(this);
    }

    private void DisposeHttpResources()
    {
        this._httpClient?.Dispose();
        this._httpMessageHandlerStub?.Dispose();
    }
}
