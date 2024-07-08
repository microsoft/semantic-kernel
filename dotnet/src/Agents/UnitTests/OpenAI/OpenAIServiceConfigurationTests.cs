// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIServiceConfiguration"/>.
/// </summary>
public class OpenAIServiceConfigurationTests
{
    /// <summary>
    /// Verify Open AI service configuration.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfiguration()
    {
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForOpenAI(apiKey: "testkey");

        Assert.Equal(OpenAIServiceConfiguration.OpenAIServiceType.OpenAI, config.Type);
        Assert.Equal("testkey", config.ApiKey);
        Assert.Null(config.Credential);
        Assert.Null(config.Endpoint);
        Assert.Null(config.HttpClient);
    }

    /// <summary>
    /// Verify Open AI service configuration with endpoint.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantProxyConfiguration()
    {
        using HttpClient client = new();

        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForOpenAI(apiKey: "testkey", endpoint: new Uri("https://localhost"), client);

        Assert.Equal(OpenAIServiceConfiguration.OpenAIServiceType.OpenAI, config.Type);
        Assert.Equal("testkey", config.ApiKey);
        Assert.Null(config.Credential);
        Assert.NotNull(config.Endpoint);
        Assert.Equal("https://localhost/", config.Endpoint.ToString());
        Assert.NotNull(config.HttpClient);
    }

    /// <summary>
    /// Verify Azure Open AI service configuration with API key.
    /// </summary>
    [Fact]
    public void VerifyAzureOpenAIAssistantApiKeyConfiguration()
    {
        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForAzureOpenAI(apiKey: "testkey", endpoint: new Uri("https://localhost"));

        Assert.Equal(OpenAIServiceConfiguration.OpenAIServiceType.AzureOpenAI, config.Type);
        Assert.Equal("testkey", config.ApiKey);
        Assert.Null(config.Credential);
        Assert.NotNull(config.Endpoint);
        Assert.Equal("https://localhost/", config.Endpoint.ToString());
        Assert.Null(config.HttpClient);
    }

    /// <summary>
    /// Verify Azure Open AI service configuration with API key.
    /// </summary>
    [Fact]
    public void VerifyAzureOpenAIAssistantCredentialConfiguration()
    {
        using HttpClient client = new();

        Mock<TokenCredential> credential = new();

        OpenAIServiceConfiguration config = OpenAIServiceConfiguration.ForAzureOpenAI(credential.Object, endpoint: new Uri("https://localhost"), client);

        Assert.Equal(OpenAIServiceConfiguration.OpenAIServiceType.AzureOpenAI, config.Type);
        Assert.Null(config.ApiKey);
        Assert.NotNull(config.Credential);
        Assert.NotNull(config.Endpoint);
        Assert.Equal("https://localhost/", config.Endpoint.ToString());
        Assert.NotNull(config.HttpClient);
    }
}
