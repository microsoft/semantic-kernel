// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletion;

/// <summary>
/// Unit tests of <see cref="AzureChatCompletion"/>.
/// </summary>
public sealed class AzureChatCompletionTests
{
    private const string ModelId = "gpt-35-turbo";
    private const string Endpoint = "https://localhost:5000";
    private const string ApiKey = "mock-api-key";
    private const string DefaultApiVersion = "2022-12-01";
    private const string ChatApiVersion = "2023-03-15-preview";

    /// <summary>
    /// Verifies that <see cref="AzureChatCompletion.GenerateMessageAsync(ChatHistory, ChatRequestSettings, System.Threading.CancellationToken)"/>
    /// returns expected message without errors
    /// </summary>
    /// <returns>Test result</returns>
    /// 
    [Fact]
    public async Task ItReturnsMessageCorrectlyAsync()
    {
        // Arrange
        const string user = "Hello!";
        ChatRequestSettings settings = new();
        using HttpResponseMessage response = new(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_test_response.json"))
        };

        using var service = this.CreateService(response);

        var history = (OpenAIChatHistory)service.CreateNewChat();
        history.AddUserMessage(user);

        // Act
        var message = await service.GenerateMessageAsync(history, settings);

        // Assert
        Assert.Equal("Hello there, how may I assist you today?", message);
    }

    private AzureChatCompletion CreateService(HttpResponseMessage responseMessage)
    {
        var loggerMock = new Mock<ILogger>();
        var delegatingHandlerFactoryMock = OpenAITestHelper.GetAzureDelegatingHandlerFactoryMock(responseMessage);
        return new AzureChatCompletion(ModelId, Endpoint, ApiKey, DefaultApiVersion, ChatApiVersion, loggerMock.Object, delegatingHandlerFactoryMock);
    }
}
