// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
using OpenAI;
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
    public void VerifyOpenAIClientProviderTargetAzureByKey()
    {
        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI(new ApiKeyCredential("key"), new Uri("https://localhost"));

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that provisioning of client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientProviderTargetAzureByCredential()
    {
        // Arrange
        Mock<TokenCredential> mockCredential = new();

        // Act
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
    public void VerifyOpenAIClientProviderTargetOpenAINoKey(string? endpoint)
    {
        // Act
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
    public void VerifyOpenAIClientProviderTargetOpenAIByKey(string key, string? endpoint)
    {
        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(key), endpoint != null ? new Uri(endpoint) : null);

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientProviderWithHttpClient()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };

        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(httpClient: httpClient);

        // Assert
        Assert.NotNull(provider.Client);

        // Arrange
        using HttpClient httpClientWithHeaders = new() { BaseAddress = new Uri("http://myproxy:9819") };
        httpClientWithHeaders.DefaultRequestHeaders.Add("X-Test", "Test");

        // Act
        OpenAIClientProvider providerWithHeaders = OpenAIClientProvider.ForOpenAI(httpClient: httpClientWithHeaders);

        // Assert
        Assert.NotNull(providerWithHeaders.Client);

        Assert.NotEqual(provider.ConfigurationKeys.Count, providerWithHeaders.ConfigurationKeys.Count);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientProviderWithHttpClientHeaders()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };
        httpClient.DefaultRequestHeaders.Add("X-Test", "Test");

        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(httpClient: httpClient);

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that the factory can accept an client that already exists.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientProviderFromClient()
    {
        // Arrange
        Mock<OpenAIClient> mockClient = new();
        OpenAIClientProvider provider = OpenAIClientProvider.FromClient(mockClient.Object);

        // Assert
        Assert.NotNull(provider.Client);
        Assert.Equal(mockClient.Object, provider.Client);
    }
}
