// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using SemanticKernel.UnitTests;

namespace SemanticKernel.IntegrationTests.CrossLanguage;

/// <summary>
/// A helper class to trace the HTTP requests made by the kernel.
/// </summary>
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

    private const string DummyStreamingResponse = @"
    data: {""id"":""chatcmpl-96fqQVHGjG9Yzs4ZMB1K6nfy2oEoo"",""object"":""chat.completion.chunk"",""created"":1711377846,""model"":""gpt-4-0125-preview"",""system_fingerprint"":""fp_a7daf7c51e"",""choices"":[{""index"":0,""delta"":{""content"":""Test chat streaming response""},""logprobs"":null,""finish_reason"":null}]}

    data: {""id"":""chatcmpl-96fqQVHGjG9Yzs4ZMB1K6nfy2oEoo"",""object"":""chat.completion.chunk"",""created"":1711377846,""model"":""gpt-4-0125-preview"",""system_fingerprint"":""fp_a7daf7c51e"",""choices"":[{""index"":0,""delta"":{},""logprobs"":null,""finish_reason"":""stop""}]}

    data: [DONE]
    ";

    private HttpClient? _httpClient;
    private HttpMessageHandlerStub? _httpMessageHandlerStub;
    private MemoryStream? _stream;

    public Kernel GetNewKernel(bool isStreaming)
    {
        this.ResetHttpComponents(isStreaming);

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

    public static async Task RunPromptAsync(Kernel kernel, bool isInline, bool isStreaming, string templateFormat, string prompt, KernelArguments? args = null)
    {
        if (isInline)
        {
            var function = KernelFunctionFactory.CreateFromPrompt(prompt);
            await RunFunctionAsync(kernel, isStreaming, function, args);
        }
        else
        {
            var promptTemplateFactory = new AggregatorPromptTemplateFactory(
                                                new KernelPromptTemplateFactory(),
                                                new HandlebarsPromptTemplateFactory());

            var function = kernel.CreateFunctionFromPrompt(
                                promptConfig: new PromptTemplateConfig()
                                {
                                    Template = prompt,
                                    TemplateFormat = templateFormat,
                                    Name = "MyFunction",
                                },
                                promptTemplateFactory: promptTemplateFactory
                            );

            await RunFunctionAsync(kernel, isStreaming, function, args);
        }
    }

    public static async Task RunFunctionAsync(Kernel kernel, bool isStreaming, KernelFunction function, KernelArguments? args = null)
    {
        if (isStreaming)
        {
            try
            {
                await foreach (var update in kernel.InvokeStreamingAsync(function, arguments: args))
                {
                    // Do nothing with received response
                }
            }
            catch (NotSupportedException)
            {
                // Ignore this exception
            }
        }
        else
        {
            await kernel.InvokeAsync(function, args);
        }
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
        this._stream?.Dispose();
    }

    private void ResetHttpComponents(bool isStreaming)
    {
        this.DisposeHttpResources();

        this._httpMessageHandlerStub = new HttpMessageHandlerStub();
        if (isStreaming)
        {
            this._stream = new MemoryStream(Encoding.UTF8.GetBytes(DummyStreamingResponse));
            this._httpMessageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(this._stream)
            };
        }
        else
        {
            this._httpMessageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(DummyResponse, Encoding.UTF8, "application/json")
            };
        }
        this._httpClient = new HttpClient(this._httpMessageHandlerStub);
    }
}
