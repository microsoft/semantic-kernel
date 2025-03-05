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

public sealed class VertexAIGeminiChatCompletionServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VertexAIGeminiChatCompletionServiceTests()
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
    public void AttributesShouldContainModelIdBearerAsString()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new VertexAIGeminiChatCompletionService(model, "key", "location", "project");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsFunc()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new VertexAIGeminiChatCompletionService(model, () => new ValueTask<string>("key"), "location", "project");

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
        var sut = new VertexAIGeminiChatCompletionService(model, () => new ValueTask<string>("key"), "location", "project", httpClient: this._httpClient);

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

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
