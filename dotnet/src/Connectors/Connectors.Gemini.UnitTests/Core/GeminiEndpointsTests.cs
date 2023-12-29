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
    public void GetGenerateContentEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetGenerateContentEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public void GetStreamGenerateContentEndpointContainsModelsBaseAndModelAndApiKey()
    {
        // Arrange
        string modelId = "fake-modelId";
        string apiKey = "fake-apiKey";

        // Act
        Uri uri = GeminiEndpoints.GetStreamGenerateContentEndpoint(modelId, apiKey);

        // Assert
        Assert.Contains(GeminiEndpoints.ModelsEndpoint.AbsoluteUri, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(modelId, uri.AbsoluteUri, StringComparison.Ordinal);
        Assert.Contains(apiKey, uri.AbsoluteUri, StringComparison.Ordinal);
    }
}
