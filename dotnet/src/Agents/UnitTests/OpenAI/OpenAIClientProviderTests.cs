// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIClientProvider"/>.
/// </summary>
public class OpenAIClientProviderTests
{
    /// <summary>
    /// Verify that provisioning of client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryTargetAzureByKey()
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI("key", new Uri("https://localhost"));

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that provisioning of client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryTargetAzureByCredential()
    {
        // Arrange
        Mock<TokenCredential> mockCredential = new();
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI(mockCredential.Object, new Uri("https://localhost"));

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that provisioning of client for OpenAI.
    /// </summary>
    [Theory]
    [InlineData(null)]
    [InlineData("http://myproxy:9819")]
    public void VerifyOpenAIClientFactoryTargetOpenAINoKey(string? endpoint)
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(endpoint != null ? new Uri(endpoint) : null);

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that provisioning of client for OpenAI.
    /// </summary>
    [Theory]
    [InlineData("key", null)]
    [InlineData("key", "http://myproxy:9819")]
    public void VerifyOpenAIClientFactoryTargetOpenAIByKey(string key, string? endpoint)
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(key, endpoint != null ? new Uri(endpoint) : null);

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryWithHttpClient()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(httpClient: httpClient);

        // Assert
        Assert.NotNull(provider.Client);
    }
}
