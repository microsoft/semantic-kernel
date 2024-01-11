#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.GoogleAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.GoogleAI;

public sealed class GoogleAIGeminiEndpointProviderTests
{
    [Fact]
    public void ModelsEndpointStartsWithBaseEndpoint()
    {
        Assert.StartsWith(
            GoogleAIGeminiEndpointProvider.BaseEndpoint.AbsoluteUri,
            GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri,
            StringComparison.Ordinal);
    }

    [Fact]
    public void GetTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetStreamTextGenerationEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetStreamChatCompletionEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetEmbeddingsEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetEmbeddingsEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetCountTokensEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";
        GoogleAIGeminiEndpointProvider sut = new(apiKey);

        // Act
        Uri uri = sut.GetCountTokensEndpoint(modelId);

        // Assert
        Assert.Contains(GoogleAIGeminiEndpointProvider.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
