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

public sealed class GoogleAIEmbeddingGeneratorTests : IDisposable
{
    private const string Model = "fake-model";
    private const string ApiKey = "fake-key";
    private const int Dimensions = 512;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public GoogleAIEmbeddingGeneratorTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(
                    """
                    {
                        "embeddings": [
                            {
                                "values": [0.1, 0.2, 0.3, 0.4, 0.5]
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
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        using var service = new GoogleAIEmbeddingGenerator(Model, ApiKey);

        // Assert
        Assert.Equal(Model, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void AttributesShouldNotContainDimensionsWhenNotProvided()
    {
        // Arrange & Act
        using var service = new GoogleAIEmbeddingGenerator(Model, ApiKey);

        // Assert
        Assert.Null(service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
    }

    [Fact]
    public void AttributesShouldContainDimensionsWhenProvided()
    {
        // Arrange & Act
        using var service = new GoogleAIEmbeddingGenerator(Model, ApiKey, dimensions: Dimensions);

        // Assert
        Assert.Equal(Dimensions, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
    }

    [Fact]
    public void GetDimensionsReturnsCorrectValue()
    {
        // Arrange
        using var service = new GoogleAIEmbeddingGenerator(Model, ApiKey, dimensions: Dimensions);

        // Act
        var result = service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions;

        // Assert
        Assert.Equal(Dimensions, result);
    }

    [Fact]
    public void GetDimensionsReturnsNullWhenNotProvided()
    {
        // Arrange
        using var service = new GoogleAIEmbeddingGenerator(Model, ApiKey);

        // Act
        var result = service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions;

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task ShouldNotIncludeDimensionsInRequestWhenNotProvidedAsync()
    {
        // Arrange
        using var service = new GoogleAIEmbeddingGenerator(
            modelId: Model,
            apiKey: ApiKey,
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
        using var service = new GoogleAIEmbeddingGenerator(
            modelId: Model,
            apiKey: ApiKey,
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
