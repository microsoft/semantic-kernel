// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Services;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextToImageService"/> class.
/// </summary>
public sealed class AzureOpenAITextToImageServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAITextToImageServiceTests()
    {
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-to-image-response.txt"))
            }
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ConstructorsAddRequiredMetadata()
    {
        // Case #1
        var sut = new AzureOpenAITextToImageService("deployment", "https://api-host/", "api-key", "model", loggerFactory: this._mockLoggerFactory.Object);
        Assert.Equal("deployment", sut.Attributes[AzureClientCore.DeploymentNameKey]);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);

        // Case #2
        sut = new AzureOpenAITextToImageService("deployment", "https://api-hostapi/", new Mock<TokenCredential>().Object, "model", loggerFactory: this._mockLoggerFactory.Object);
        Assert.Equal("deployment", sut.Attributes[AzureClientCore.DeploymentNameKey]);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);

        // Case #3
        sut = new AzureOpenAITextToImageService("deployment", new AzureOpenAIClient(new Uri("https://api-host/"), new ApiKeyCredential("api-key")), "model", loggerFactory: this._mockLoggerFactory.Object);
        Assert.Equal("deployment", sut.Attributes[AzureClientCore.DeploymentNameKey]);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(256, 256, "dall-e-2")]
    [InlineData(512, 512, "dall-e-2")]
    [InlineData(1024, 1024, "dall-e-2")]
    [InlineData(1024, 1024, "dall-e-3")]
    [InlineData(1024, 1792, "dall-e-3")]
    [InlineData(1792, 1024, "dall-e-3")]
    [InlineData(123, 321, "custom-model-1")]
    [InlineData(179, 124, "custom-model-2")]
    public async Task GenerateImageWorksCorrectlyAsync(int width, int height, string modelId)
    {
        // Arrange
        var sut = new AzureOpenAITextToImageService("deployment", "https://api-host", "api-key", modelId, this._httpClient, loggerFactory: this._mockLoggerFactory.Object);

        // Act 
        var result = await sut.GenerateImageAsync("description", width, height);

        // Assert
        Assert.Equal("https://image-url/", result);

        var request = JsonSerializer.Deserialize<JsonObject>(this._messageHandlerStub.RequestContent); // {"prompt":"description","model":"deployment","response_format":"url","size":"179x124"}
        Assert.NotNull(request);
        Assert.Equal("description", request["prompt"]?.ToString());
        Assert.Equal("deployment", request["model"]?.ToString());
        Assert.Equal("url", request["response_format"]?.ToString());
        Assert.Equal($"{width}x{height}", request["size"]?.ToString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItShouldUseProvidedEndpoint(bool useTokeCredential)
    {
        // Arrange
        var sut = useTokeCredential ?
            new AzureOpenAITextToImageService("deployment", endpoint: "https://api-host", new Mock<TokenCredential>().Object, "dall-e-3", this._httpClient) :
            new AzureOpenAITextToImageService("deployment", endpoint: "https://api-host", "api-key", "dall-e-3", this._httpClient);

        // Act
        var result = await sut.GenerateImageAsync("description", 1024, 1024);

        // Assert
        Assert.StartsWith("https://api-host", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Theory]
    [InlineData(true, "")]
    [InlineData(true, null)]
    [InlineData(false, "")]
    [InlineData(false, null)]
    public async Task ItShouldUseHttpClientUriIfNoEndpointProvided(bool useTokeCredential, string? endpoint)
    {
        // Arrange
        this._httpClient.BaseAddress = new Uri("https://api-host");

        var sut = useTokeCredential ?
            new AzureOpenAITextToImageService("deployment", endpoint: endpoint!, new Mock<TokenCredential>().Object, "dall-e-3", this._httpClient) :
            new AzureOpenAITextToImageService("deployment", endpoint: endpoint!, "api-key", "dall-e-3", this._httpClient);

        // Act
        var result = await sut.GenerateImageAsync("description", 1024, 1024);

        // Assert
        Assert.StartsWith("https://api-host", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Theory]
    [InlineData(true, "")]
    [InlineData(true, null)]
    [InlineData(false, "")]
    [InlineData(false, null)]
    public void ItShouldThrowExceptionIfNoEndpointProvided(bool useTokeCredential, string? endpoint)
    {
        // Arrange
        this._httpClient.BaseAddress = null;

        // Act & Assert
        if (useTokeCredential)
        {
            Assert.Throws<ArgumentException>(() => new AzureOpenAITextToImageService("deployment", endpoint: endpoint!, new Mock<TokenCredential>().Object, "dall-e-3", this._httpClient));
        }
        else
        {
            Assert.Throws<ArgumentException>(() => new AzureOpenAITextToImageService("deployment", endpoint: endpoint!, "api-key", "dall-e-3", this._httpClient));
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
