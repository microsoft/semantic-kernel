// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIResponsesAgent"/>.
/// </summary>
#pragma warning disable CS0419 // Ambiguous reference in cref attribute
public sealed class OpenAIResponsesAgentTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of objects required to test a <see cref="OpenAIResponsesAgent"/>.
    /// </summary>
    public OpenAIResponsesAgentTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._kernel = new Kernel();

        var options = new OpenAIClientOptions
        {
            Transport = new HttpClientPipelineTransport(this._httpClient)
        };
        this._client = new(model: "gpt-4o", credential: new ApiKeyCredential("apikey"), options: options);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }

    /// <summary>
    /// Verify InvokeAsync
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        OpenAIResponsesAgent agent = new(this._client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
        };

        // Act
        var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France?"));

        // Assert
        Assert.NotNull(responseItems);
        var messages = await responseItems.ToListAsync();
        Assert.Single(messages);
        Assert.Equal("The capital of France is Paris.\n\nLa capitale de la France est Paris.", messages[0].Message.Content);
    }

    #region private
    private const string WhatIsTheSKResponseJson = "./TestData/openai_responses_what_is_the_semantic_kernel.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;
    private readonly OpenAIResponseClient _client;
    #endregion
}
