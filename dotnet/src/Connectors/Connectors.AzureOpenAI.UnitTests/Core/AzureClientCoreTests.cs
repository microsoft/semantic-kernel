// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Core;

public sealed class AzureClientCoreTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly Mock<ILogger> _mockLogger;

    public AzureClientCoreTests()
    {
        this._httpClient = new HttpClient();
        this._mockLogger = new Mock<ILogger>();
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    [Fact]
    public void ConstructorWithValidParametersShouldInitializeCorrectly()
    {
        // Arrange
        var deploymentName = "test-deployment";
        var endpoint = "https://test-endpoint.openai.azure.com/";
        var apiKey = "test-api-key";

        // Act
        var azureClientCore = new AzureClientCore(deploymentName, endpoint, apiKey, this._httpClient, this._mockLogger.Object);

        // Assert
        Assert.NotNull(azureClientCore.Client);
        Assert.Equal(deploymentName, azureClientCore.DeploymentName);
        Assert.Equal(new Uri(endpoint), azureClientCore.Endpoint);
    }

    [Fact]
    public void ConstructorWithInvalidEndpointShouldThrowArgumentException()
    {
        // Arrange
        var deploymentName = "test-deployment";
        var invalidEndpoint = "http://invalid-endpoint";
        var apiKey = "test-api-key";

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            new AzureClientCore(deploymentName, invalidEndpoint, apiKey, this._httpClient, this._mockLogger.Object));
    }

    [Fact]
    public void ConstructorWithTokenCredentialShouldInitializeCorrectly()
    {
        // Arrange
        var deploymentName = "test-deployment";
        var endpoint = "https://test-endpoint.openai.azure.com/";
        var tokenCredential = new Mock<TokenCredential>().Object;

        // Act
        var azureClientCore = new AzureClientCore(deploymentName, endpoint, tokenCredential, this._httpClient, this._mockLogger.Object);

        // Assert
        Assert.NotNull(azureClientCore.Client);
        Assert.Equal(deploymentName, azureClientCore.DeploymentName);
        Assert.Equal(new Uri(endpoint), azureClientCore.Endpoint);
    }

    [Fact]
    public void ConstructorWithOpenAIClientShouldInitializeCorrectly()
    {
        // Arrange
        var deploymentName = "test-deployment";
        var openAIClient = new Mock<AzureOpenAIClient>(MockBehavior.Strict, new Uri("https://test-endpoint.openai.azure.com/"), new Mock<TokenCredential>().Object).Object;

        // Act
        var azureClientCore = new AzureClientCore(deploymentName, openAIClient, this._mockLogger.Object);

        // Assert
        Assert.NotNull(azureClientCore.Client);
        Assert.Equal(deploymentName, azureClientCore.DeploymentName);
    }
}
