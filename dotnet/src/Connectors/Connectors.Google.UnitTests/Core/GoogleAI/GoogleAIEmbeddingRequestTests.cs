// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.GoogleAI;

public sealed class GoogleAIEmbeddingRequestTests
{
    // Arrange
    private static readonly string[] s_data = ["text1", "text2"];
    private const string ModelId = "modelId";
    private const string DimensionalityJsonPropertyName = "\"outputDimensionality\"";
    private const int Dimensions = 512;

    [Fact]
    public void FromDataReturnsValidRequestWithData()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Equal(s_data[0], request.Requests[0].Content.Parts![0].Text);
        Assert.Equal(s_data[1], request.Requests[1].Content.Parts![0].Text);
    }

    [Fact]
    public void FromDataReturnsValidRequestWithModelId()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Equal($"models/{ModelId}", request.Requests[0].Model);
        Assert.Equal($"models/{ModelId}", request.Requests[1].Model);
    }

    [Fact]
    public void FromDataSetsDimensionsToNullWhenNotProvided()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Null(request.Requests[0].Dimensions);
        Assert.Null(request.Requests[1].Dimensions);
    }

    [Fact]
    public void FromDataJsonDoesNotIncludeDimensionsWhenNull()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId);
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.DoesNotContain(DimensionalityJsonPropertyName, json);
    }

    [Fact]
    public void FromDataSetsDimensionsWhenProvided()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId, Dimensions);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Equal(Dimensions, request.Requests[0].Dimensions);
        Assert.Equal(Dimensions, request.Requests[1].Dimensions);
    }

    [Fact]
    public void FromDataJsonIncludesDimensionsWhenProvided()
    {
        // Act
        var request = GoogleAIEmbeddingRequest.FromData(s_data, ModelId, Dimensions);
        string json = JsonSerializer.Serialize(request);

        // Assert
        Assert.Contains($"{DimensionalityJsonPropertyName}:{Dimensions}", json);
    }
}
