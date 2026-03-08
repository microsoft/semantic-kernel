// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net.Http;
using OpenAI;
using OpenAI.Responses;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Base tests which use <see cref="ResponsesClient"/>
/// </summary>
public class BaseOpenAIResponseClientTest : IDisposable
{
    internal MultipleHttpMessageHandlerStub MessageHandlerStub { get; }
    internal HttpClient HttpClient { get; }
    internal ResponsesClient Client { get; }

    internal BaseOpenAIResponseClientTest()
    {
        this.MessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this.HttpClient = new HttpClient(this.MessageHandlerStub, disposeHandler: false);

        var clientOptions = new OpenAIClientOptions()
        {
            Transport = new HttpClientPipelineTransport(this.HttpClient)
        };
        this.Client = new ResponsesClient("model", new ApiKeyCredential("apiKey"), clientOptions);
    }

    /// <inheritdoc />
    public void Dispose()
    {
        this.MessageHandlerStub.Dispose();
        this.HttpClient.Dispose();

        GC.SuppressFinalize(this);
    }
}
