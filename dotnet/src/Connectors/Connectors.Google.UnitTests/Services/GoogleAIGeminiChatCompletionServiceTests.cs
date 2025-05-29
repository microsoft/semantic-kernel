// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class GoogleAIGeminiChatCompletionServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public GoogleAIGeminiChatCompletionServiceTests()
    {
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/completion_one_response.json"))
            }
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new GoogleAIGeminiChatCompletionService(model, "key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("content")]
    [InlineData("")]
    public async Task RequestCachedContentWorksCorrectlyAsync(string? cachedContent)
    {
        // Arrange
        string model = "fake-model";
        var sut = new GoogleAIGeminiChatCompletionService(model, "key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetChatMessageContentAsync("my prompt", new GeminiPromptExecutionSettings { CachedContent = cachedContent });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        if (cachedContent is not null)
        {
            Assert.Contains($"\"cachedContent\":\"{cachedContent}\"", requestBody);
        }
        else
        {
            // Then no quality is provided, it should not be included in the request body
            Assert.DoesNotContain("cachedContent", requestBody);
        }
    }

    [Theory]
    [InlineData(null, false)]
    [InlineData(0, true)]
    [InlineData(500, true)]
    [InlineData(2048, true)]
    public async Task RequestBodyIncludesThinkingConfigWhenSetAsync(int? thinkingBudget, bool shouldContain)
    {
        // Arrange
        string model = "gemini-2.5-pro";
        var sut = new GoogleAIGeminiChatCompletionService(model, "key", httpClient: this._httpClient);

        var executionSettings = new GeminiPromptExecutionSettings
        {
            ThinkingConfig = thinkingBudget.HasValue
                ? new GeminiThinkingConfig { ThinkingBudget = thinkingBudget.Value }
                : null
        };

        // Act
        var result = await sut.GetChatMessageContentAsync("my prompt", executionSettings);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        if (shouldContain)
        {
            Assert.Contains("thinkingConfig", requestBody);
            Assert.Contains($"\"thinkingBudget\":{thinkingBudget}", requestBody);
        }
        else
        {
            Assert.DoesNotContain("thinkingConfig", requestBody);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
