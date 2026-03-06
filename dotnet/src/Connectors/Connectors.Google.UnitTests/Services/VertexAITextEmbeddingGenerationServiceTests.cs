// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

[Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
public sealed class VertexAITextEmbeddingGenerationServiceTests : IDisposable
{
    private const string Model = "fake-model";
    private const string BearerKey = "fake-key";
    private const int Dimensions = 512;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VertexAITextEmbeddingGenerationServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(
                    """
                    {
                        "predictions": [
                            {
                                "embeddings": {
                                    "values": [0.1, 0.2, 0.3, 0.4, 0.5]
                                }
                            }
                        ]
                    }
                    """,
                    Encoding.UTF8,
                    "application/json"
                )
            }
        };

        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsString()
    {
        // Arrange & Act
        var service = new VertexAITextEmbeddingGenerationService(Model, BearerKey, "location", "project");

        // Assert
        Assert.Equal(Model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsFunc()
    {
        // Arrange & Act
        var service = new VertexAITextEmbeddingGenerationService(Model, () => ValueTask.FromResult(BearerKey), "location", "project");

        // Assert
        Assert.Equal(Model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldNotContainDimensionsWhenNotProvided()
    {
        // Arrange & Act
        var service = new VertexAITextEmbeddingGenerationService(Model, BearerKey, "location", "project");

        // Assert
        Assert.False(service.Attributes.ContainsKey(EmbeddingGenerationExtensions.DimensionsKey));
    }

    [Fact]
    public void AttributesShouldContainDimensionsWhenProvided()
    {
        // Arrange & Act
        var service = new VertexAITextEmbeddingGenerationService(Model, BearerKey, "location", "project", dimensions: Dimensions);

        // Assert
        Assert.Equal(Dimensions, service.Attributes[EmbeddingGenerationExtensions.DimensionsKey]);
    }

    [Fact]
    public void GetDimensionsReturnsCorrectValue()
    {
        // Arrange
        var service = new VertexAITextEmbeddingGenerationService(Model, BearerKey, "location", "project", dimensions: Dimensions);

        // Act
        var result = service.GetDimensions();

        // Assert
        Assert.Equal(Dimensions, result);
    }

    [Fact]
    public void GetDimensionsReturnsNullWhenNotProvided()
    {
        // Arrange
        var service = new VertexAITextEmbeddingGenerationService(Model, BearerKey, "location", "project");

        // Act
        var result = service.GetDimensions();

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task ShouldNotIncludeDimensionsInRequestWhenNotProvidedAsync()
    {
        // Arrange
        var service = new VertexAITextEmbeddingGenerationService(
            modelId: Model,
            bearerKey: BearerKey,
            location: "location",
            projectId: "project",
            dimensions: null,
            httpClient: this._httpClient);
        var dataToEmbed = new List<string> { "Text to embed" };

        // Act
        await service.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.DoesNotContain("outputDimensionality", requestBody);
    }

    [Theory]
    [InlineData(Dimensions)]
    [InlineData(Dimensions * 2)]
    public async Task ShouldIncludeDimensionsInRequestWhenProvidedAsync(int? dimensions)
    {
        // Arrange
        var service = new VertexAITextEmbeddingGenerationService(
            modelId: Model,
            bearerKey: BearerKey,
            location: "location",
            projectId: "project",
            dimensions: dimensions,
            httpClient: this._httpClient);
        var dataToEmbed = new List<string> { "Text to embed" };

        // Act
        await service.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains($"\"outputDimensionality\":{dimensions}", requestBody);
    }

    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }
}
