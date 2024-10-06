<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
using System;
=======
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
using System;
=======
// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
>>>>>>> main
>>>>>>> Stashed changes
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
using OpenAI;
6d73513a859ab2d05e01db3bc1d405827799e34b
using OpenAI;
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    public void VerifyOpenAIClientFactoryTargetAzureByKey()
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI("key", new Uri("https://localhost"));
=======
<<<<<<< HEAD
    public void VerifyOpenAIClientFactoryTargetAzureByKey()
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI("key", new Uri("https://localhost"));
=======
    public void VerifyOpenAIClientProviderTargetAzureByKey()
    {
        // Act
    public void VerifyOpenAIClientFactoryTargetAzureByKey()
    {
        // Arrange
 6d73513a859ab2d05e01db3bc1d405827799e34b
    public void VerifyOpenAIClientProviderTargetAzureByKey()
    {
        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI("key", new Uri("https://localhost"));
        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI(new ApiKeyCredential("key"), new Uri("https://localhost"));
>>>>>>> main
>>>>>>> Stashed changes

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that provisioning of client for Azure OpenAI.
    /// </summary>
    [Fact]
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
    public void VerifyOpenAIClientProviderTargetAzureByCredential()
    {
        // Arrange
        Mock<TokenCredential> mockCredential = new();

        // Act
>>>>>>> main
>>>>>>> Stashed changes
    public void VerifyOpenAIClientFactoryTargetAzureByCredential()
    {
        // Arrange
        Mock<TokenCredential> mockCredential = new();
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
 6d73513a859ab2d05e01db3bc1d405827799e34b
    public void VerifyOpenAIClientProviderTargetAzureByCredential()
    {
        // Arrange
        Mock<TokenCredential> mockCredential = new();

        // Act
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    public void VerifyOpenAIClientFactoryTargetOpenAINoKey(string? endpoint)
    {
        // Arrange
=======
<<<<<<< HEAD
    public void VerifyOpenAIClientFactoryTargetOpenAINoKey(string? endpoint)
    {
        // Arrange
=======
    public void VerifyOpenAIClientProviderTargetOpenAINoKey(string? endpoint)
    {
        // Act
    public void VerifyOpenAIClientFactoryTargetOpenAINoKey(string? endpoint)
    {
        // Arrange
 6d73513a859ab2d05e01db3bc1d405827799e34b
    public void VerifyOpenAIClientProviderTargetOpenAINoKey(string? endpoint)
    {
        // Act
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    public void VerifyOpenAIClientFactoryTargetOpenAIByKey(string key, string? endpoint)
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(key, endpoint != null ? new Uri(endpoint) : null);
=======
<<<<<<< HEAD
    public void VerifyOpenAIClientFactoryTargetOpenAIByKey(string key, string? endpoint)
    {
        // Arrange
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(key, endpoint != null ? new Uri(endpoint) : null);
=======
    public void VerifyOpenAIClientProviderTargetOpenAIByKey(string key, string? endpoint)
    {
        // Act
    public void VerifyOpenAIClientFactoryTargetOpenAIByKey(string key, string? endpoint)
    {
        // Arrange
 6d73513a859ab2d05e01db3bc1d405827799e34b
    public void VerifyOpenAIClientProviderTargetOpenAIByKey(string key, string? endpoint)
    {
        // Act
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(key, endpoint != null ? new Uri(endpoint) : null);
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(key), endpoint != null ? new Uri(endpoint) : null);
>>>>>>> main
>>>>>>> Stashed changes

        // Assert
        Assert.NotNull(provider.Client);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
    public void VerifyOpenAIClientProviderWithHttpClient()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };

        // Act
>>>>>>> main
>>>>>>> Stashed changes
    public void VerifyOpenAIClientFactoryWithHttpClient()
    {
        // Arrange
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
 6d73513a859ab2d05e01db3bc1d405827799e34b
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
        httpClient.DefaultRequestHeaders.Add("X-Test", "Test");

        // Act
        OpenAIClientProvider providerWithHeaders = OpenAIClientProvider.ForOpenAI(httpClient: httpClient);

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
>>>>>>> main
>>>>>>> Stashed changes
        OpenAIClientProvider provider = OpenAIClientProvider.ForOpenAI(httpClient: httpClient);

        // Assert
        Assert.NotNull(provider.Client);
    }
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======

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
 6d73513a859ab2d05e01db3bc1d405827799e34b
    }
>>>>>>> main
>>>>>>> Stashed changes
}
