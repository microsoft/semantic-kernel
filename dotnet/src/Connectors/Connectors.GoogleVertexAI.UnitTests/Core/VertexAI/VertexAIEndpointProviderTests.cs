// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.VertexAI;

public sealed class VertexAIEndpointProviderTests
{
    [Fact]
    public void ModelsEndpointStartsWithBaseEndpoint()
    {
        // Arrange
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act & Assert
        Assert.StartsWith(
            sut.BaseEndpoint.AbsoluteUri,
            sut.ModelsEndpoint.AbsoluteUri,
            StringComparison.Ordinal);
    }

    [Fact]
    public void BaseEndpointContainsLocation()
    {
        // Arrange
        string location = "fake-location";
        var sut = new VertexAIEndpointProvider(new(location: location, projectId: "fake-projectId"));

        // Act & Assert
        Assert.Contains(location, sut.BaseEndpoint.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void BaseEndpointContainsProjectId()
    {
        // Arrange
        string projectId = "fake-projectId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: projectId));

        // Act & Assert
        Assert.Contains(projectId, sut.BaseEndpoint.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiTextGenerationEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetGeminiTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiStreamTextGenerationEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetGeminiStreamTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiChatCompletionEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetGeminiChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiStreamChatCompletionEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetGeminiStreamChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetEmbeddingsEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetEmbeddingsEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetCountTokensEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetCountTokensEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
