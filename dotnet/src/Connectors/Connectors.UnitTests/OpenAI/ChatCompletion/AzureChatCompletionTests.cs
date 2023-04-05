// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Reliability;
using SemanticKernel.Connectors.UnitTests.HuggingFace;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletion;
/// <summary>
/// Unit tests of <see cref="AzureChatCompletion"/>.
/// </summary>
public class AzureChatCompletionTests : IDisposable
{
    private const string ModelId = "gpt-35-turbo";
    private const string Endpoint = "https://localhost:5000";
    private const string ApiKey = "mock-api-key";
    private const string DefaultApiVersion = "2022-12-01";
    private const string ChatApiVersion = "2023-03-15-preview";

    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = System.Net.HttpStatusCode.OK,
    };

    /// <summary>
    /// Verifies that <see cref="AzureChatCompletion.GenerateMessageAsync(ChatHistory, ChatRequestSettings, System.Threading.CancellationToken)"/>
    /// returns expected message without errors
    /// </summary>
    /// <returns></returns>
    /// 
    [Fact]
    public async Task ItReturnsMessageCorrectlyAsync()
    {
        // Arrange
        const string user = "Hello!";
        ChatRequestSettings settings = new();
        using var service = this.CreateService(OpenAITestHelper.GetTestResponse("chat_test_response.json"));
        var history = (OpenAIChatHistory)service.CreateNewChat();
        history.AddUserMessage(user);

        // Act
        var message = await service.GenerateMessageAsync(history, settings);


        // Assert
        Assert.Equal("Hello there, how may I assist you today?", message);
    }

    private AzureChatCompletion CreateService(string testMessage)
    {
        this._response.Content = new StringContent(testMessage);
        var delegatingHandlerFactory = OpenAITestHelper.GetAzureDelegatingHandlerFactoryMock(this._response);
        return new AzureChatCompletion(ModelId, Endpoint, ApiKey, DefaultApiVersion, ChatApiVersion, handlerFactory: delegatingHandlerFactory);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._response.Dispose();
        }
    }
}
