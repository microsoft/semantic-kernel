#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using Microsoft.SemanticKernel.Connectors.Gemini.Core.VertexAI;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core.VertexAI;

public sealed class VertexAIGeminiEndpointProviderTests
{
    [Fact]
    public void ModelsEndpointStartsWithBaseEndpoint()
    {
        // Arrange
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

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
        var sut = new VertexAIGeminiEndpointProvider(new(location: location, projectId: "fake-projectId"));

        // Act & Assert
        Assert.Contains(location, sut.BaseEndpoint.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void BaseEndpointContainsProjectId()
    {
        // Arrange
        string projectId = "fake-projectId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: projectId));

        // Act & Assert
        Assert.Contains(projectId, sut.BaseEndpoint.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetTextGenerationEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamTextGenerationEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetStreamTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetChatCompletionEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamChatCompletionEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetStreamChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetEmbeddingsEndpointContainsModelsBaseAndModel()
    {
        // Arrange
        string modelId = "fake-modelId";
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

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
        var sut = new VertexAIGeminiEndpointProvider(new(location: "fake-location", projectId: "fake-projectId"));

        // Act
        Uri uri = sut.GetCountTokensEndpoint(modelId);

        // Assert
        Assert.Contains(sut.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
