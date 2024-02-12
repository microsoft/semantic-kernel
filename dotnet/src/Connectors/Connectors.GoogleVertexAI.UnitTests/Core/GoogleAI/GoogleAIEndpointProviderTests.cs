// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.GoogleAI;

public sealed class GoogleAIEndpointProviderTests
{
    [Fact]
    public void ModelsEndpointStartsWithBaseEndpoint()
    {
        Assert.StartsWith(
            GoogleAIEndpointProvider.BaseEndpoint.AbsoluteUri,
            GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri,
            StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetGeminiTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiStreamTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetGeminiStreamTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetGeminiChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetGeminiStreamChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetGeminiStreamChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetEmbeddingsEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetEmbeddingsEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetCountTokensEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetCountTokensEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
