#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core;

public class GeminiEndpointsTests
{
    [Fact]
    public void ModelsEndpointStartsWithBaseEndpoint()
    {
        Assert.StartsWith(
            GeminiEndpoints.BaseEndpoint.AbsoluteUri,
            GeminiEndpoints.ModelsEndpoint.AbsoluteUri,
            StringComparison.Ordinal);
    }

    [Fact]
    public void GetTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetTextGenerationEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamTextGenerationEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetStreamTextGenerationEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetChatCompletionEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamChatCompletionEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetStreamChatCompletionEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
