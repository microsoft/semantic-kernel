// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Connectors.Google;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class VertexAIEmbeddingGeneratorTests : IDisposable
{
    private const string Model = "fake-model";
    private const string BearerKey = "fake-key";
    private const int Dimensions = 512;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public VertexAIEmbeddingGeneratorTests()
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
        using var service = new VertexAIEmbeddingGenerator(Model, BearerKey, "location", "project");

        // Assert
        Assert.Equal(Model, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsFunc()
    {
        // Arrange & Act
        using var service = new VertexAIEmbeddingGenerator(Model, () => ValueTask.FromResult(BearerKey), "location", "project");

        // Assert
        Assert.Equal(Model, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void AttributesShouldNotContainDimensionsWhenNotProvided()
    {
        // Arrange & Act
        using var service = new VertexAIEmbeddingGenerator(Model, BearerKey, "location", "project");

        // Assert
        Assert.Null(service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
    }

    [Fact]
    public void AttributesShouldContainDimensionsWhenProvided()
    {
        // Arrange & Act
        using var service = new VertexAIEmbeddingGenerator(Model, BearerKey, "location", "project", dimensions: Dimensions);

        // Assert
        Assert.Equal(Dimensions, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
    }

    [Fact]
    public void GetDimensionsReturnsCorrectValue()
    {
        // Arrange
        using var service = new VertexAIEmbeddingGenerator(Model, BearerKey, "location", "project", dimensions: Dimensions);

        // Act
        var result = service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions;

        // Assert
        Assert.Equal(Dimensions, result);
    }

    [Fact]
    public void GetDimensionsReturnsNullWhenNotProvided()
    {
        // Arrange
        using var service = new VertexAIEmbeddingGenerator(Model, BearerKey, "location", "project");

        // Act
        var result = service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions;

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task ShouldNotIncludeDimensionsInRequestWhenNotProvidedAsync()
    {
        // Arrange
        using var service = new VertexAIEmbeddingGenerator(
            modelId: Model,
            bearerKey: BearerKey,
            location: "location",
            projectId: "project",
            dimensions: null,
            httpClient: this._httpClient);
        var dataToEmbed = new List<string> { "Text to embed" };

        // Act
        await service.GenerateAsync(dataToEmbed);

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
        using var service = new VertexAIEmbeddingGenerator(
            modelId: Model,
            bearerKey: BearerKey,
            location: "location",
            projectId: "project",
            dimensions: dimensions,
            httpClient: this._httpClient);
        var dataToEmbed = new List<string> { "Text to embed" };

        // Act
        await service.GenerateAsync(dataToEmbed);

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
