// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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

    [Fact]
    public async Task RequestLabelsWorksCorrectlyAsync()
    {
        // Arrange
        string model = "fake-model";
        var sut = new GoogleAIGeminiChatCompletionService(model, "key", httpClient: this._httpClient);
        var labels = new Dictionary<string, string> { { "key1", "value1" }, { "key2", "value2" } };

        // Act
        var result = await sut.GetChatMessageContentAsync("my prompt", new GeminiPromptExecutionSettings { Labels = labels });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"labels\":{\"key1\":\"value1\",\"key2\":\"value2\"}", requestBody);
    }

    [Fact]
    public async Task RequestLabelsNullWorksCorrectlyAsync()
    {
        // Arrange
        string model = "fake-model";
        var sut = new GoogleAIGeminiChatCompletionService(model, "key", httpClient: this._httpClient);

        // Act
        var result = await sut.GetChatMessageContentAsync("my prompt", new GeminiPromptExecutionSettings { Labels = null });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        var requestBody = UTF8Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.DoesNotContain("labels", requestBody);
    }

    [Theory]
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

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsExceptionWithEmptyBinaryContentAsync()
    {
        // Arrange
        var sut = new GoogleAIGeminiChatCompletionService("gemini-2.5-pro", "key");

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage([new BinaryContent()]);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetChatMessageContentsThrowsExceptionUriOnlyReferenceBinaryContentAsync()
    {
        // Arrange
        var sut = new GoogleAIGeminiChatCompletionService("gemini-2.5-pro", "key");

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage([new BinaryContent(new Uri("file://testfile.pdf"))]);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => sut.GetChatMessageContentsAsync(chatHistory));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItSendsBinaryContentCorrectlyAsync(bool useUriData)
    {
        // Arrange
        var sut = new GoogleAIGeminiChatCompletionService("gemini-2.5-pro", "key", httpClient: this._httpClient);

        var mimeType = "application/pdf";
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage([
            new TextContent("What's in this file?"),
            useUriData
                ? new BinaryContent($"data:{mimeType};base64,{PdfBase64Data}")
                : new BinaryContent(Convert.FromBase64String(PdfBase64Data), mimeType)
        ]);

        // Act
        await sut.GetChatMessageContentsAsync(chatHistory);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonElement.Parse(actualRequestContent);

        var contents = optionsJson.GetProperty("contents");
        Assert.Equal(1, contents.GetArrayLength());

        var parts = contents[0].GetProperty("parts");
        Assert.Equal(2, parts.GetArrayLength());

        Assert.True(parts[0].TryGetProperty("text", out var prompt));
        Assert.Equal("What's in this file?", prompt.ToString());

        // Check for the file data
        Assert.True(parts[1].TryGetProperty("inlineData", out var inlineData));
        Assert.Equal(JsonValueKind.Object, inlineData.ValueKind);
        Assert.Equal(mimeType, inlineData.GetProperty("mimeType").GetString());
        Assert.Equal(PdfBase64Data, inlineData.GetProperty("data").ToString());
    }

    /// <summary>
    /// Sample PDF data URI for testing.
    /// </summary>
    private const string PdfBase64Data = "JVBERi0xLjQKMSAwIG9iago8PC9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlIC9QYWdlcwovS2lkcyBbMyAwIFJdCi9Db3VudCAxCj4+CmVuZG9iagozIDAgb2JqCjw8L1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA1OTUgODQyXQovQ29udGVudHMgNSAwIFIKL1Jlc291cmNlcyA8PC9Qcm9jU2V0IFsvUERGIC9UZXh0XQovRm9udCA8PC9GMSA0IDAgUj4+Cj4+Cj4+CmVuZG9iago0IDAgb2JqCjw8L1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9OYW1lIC9GMQovQmFzZUZvbnQgL0hlbHZldGljYQovRW5jb2RpbmcgL01hY1JvbWFuRW5jb2RpbmcKPj4KZW5kb2JqCjUgMCBvYmoKPDwvTGVuZ3RoIDUzCj4+CnN0cmVhbQpCVAovRjEgMjAgVGYKMjIwIDQwMCBUZAooRHVtbXkgUERGKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZgowMDAwMDAwMDA5IDAwMDAwIG4KMDAwMDAwMDA2MyAwMDAwMCBuCjAwMDAwMDAxMjQgMDAwMDAgbgowMDAwMDAwMjc3IDAwMDAwIG4KMDAwMDAwMDM5MiAwMDAwMCBuCnRyYWlsZXIKPDwvU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0OTUKJSVFT0YK";

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
