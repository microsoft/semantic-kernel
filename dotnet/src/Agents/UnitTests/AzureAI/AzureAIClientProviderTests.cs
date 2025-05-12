// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.AI.Projects.OneDP;
using Azure.Identity;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI;

/// <summary>
/// Unit testing of <see cref="AzureAIClientProvider"/>.
/// </summary>
public class AzureAIClientProviderTests
{
    /// <summary>
    /// Verify that provisioning of client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyAzureAIClientProviderDefault()
    {
        // Act
        AzureAIClientProvider provider = AzureAIClientProvider.FromEndpoint(new Uri("https://test"), new AzureCliCredential());

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
    public void VerifyAzureAIClientProviderWithHttpClient()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };

        // Act
        AzureAIClientProvider provider = AzureAIClientProvider.FromEndpoint(new Uri("https://test"), new AzureCliCredential(), httpClient);

        // Assert
        Assert.NotNull(provider.Client);

        // Arrange
        using HttpClient httpClientWithHeaders = new() { BaseAddress = new Uri("http://myproxy:9819") };
        httpClientWithHeaders.DefaultRequestHeaders.Add("X-Test", "Test");

        // Act
        AzureAIClientProvider providerWithHeaders = AzureAIClientProvider.FromEndpoint(new Uri("https://test"), new AzureCliCredential(), httpClientWithHeaders);

        // Assert
        Assert.NotNull(providerWithHeaders.Client);

        Assert.NotEqual(provider.ConfigurationKeys.Count, providerWithHeaders.ConfigurationKeys.Count);
    }

    /// <summary>
    /// Verify that the factory can accept an client that already exists.
    /// </summary>
    [Fact]
    public void VerifyAzureAIClientProviderFromClient()
    {
        // Arrange
        Mock<AIProjectClient> mockClient = new();
        AzureAIClientProvider provider = AzureAIClientProvider.FromClient(mockClient.Object);

        // Assert
        Assert.NotNull(provider.Client);
        Assert.Equal(mockClient.Object, provider.Client);
    }
}
