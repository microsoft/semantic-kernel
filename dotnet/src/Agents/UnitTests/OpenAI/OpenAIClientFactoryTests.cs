// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
using OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIClientFactory"/>.
/// </summary>
public class OpenAIClientFactoryTests
{
    /// <summary>
    /// Verify that the factory can create a client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryTargetAzureByKey()
    {
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForAzureOpenAI("key", new Uri("https://localhost"));
        OpenAIClient client = OpenAIClientFactory.CreateClient(config);
        Assert.NotNull(client);
    }

    /// <summary>
    /// Verify that the factory can create a client for Azure OpenAI.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryTargetAzureByCredential()
    {
        Mock<TokenCredential> mockCredential = new();
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForAzureOpenAI(mockCredential.Object, new Uri("https://localhost"));
        OpenAIClient client = OpenAIClientFactory.CreateClient(config);
        Assert.NotNull(client);
    }

    /// <summary>
    /// Verify that the factory can create a client for various OpenAI service configurations.
    /// </summary>
    [Theory]
    [InlineData(null, null)]
    [InlineData("key", null)]
    [InlineData("key", "http://myproxy:9819")]
    public void VerifyOpenAIClientFactoryTargetOpenAI(string? key, string? endpoint)
    {
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForOpenAI(key, endpoint != null ? new Uri(endpoint) : null);
        OpenAIClient client = OpenAIClientFactory.CreateClient(config);
        Assert.NotNull(client);
    }

    /// <summary>
    /// Verify that the factory can create a client with http proxy.
    /// </summary>
    [Fact]
    public void VerifyOpenAIClientFactoryWithHttpClient()
    {
        using HttpClient httpClient = new() { BaseAddress = new Uri("http://myproxy:9819") };
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForOpenAI(apiKey: null, httpClient: httpClient);
        OpenAIClient client = OpenAIClientFactory.CreateClient(config);
        Assert.NotNull(client);
    }
}
