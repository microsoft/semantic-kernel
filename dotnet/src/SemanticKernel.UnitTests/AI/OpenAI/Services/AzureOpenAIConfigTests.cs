// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.UnitTests.AI.OpenAI.Services;

public class AzureOpenAIConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string label = "testLabel";
        string deploymentName = "testDeploymentName";
        string endpoint = "https://testEndpoint.com";
        string apiKey = "testApiKey";
        string apiVersion = "testApiVersion";

        // Act
        var config = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        // Assert
        Assert.Equal(label, config.Label);
        Assert.Equal(deploymentName, config.DeploymentName);
        Assert.Equal(endpoint, config.Endpoint);
        Assert.Equal(apiKey, config.APIKey);
        Assert.Equal(apiVersion, config.APIVersion);
    }

    [Theory]
    [InlineData("", "testDeploymentName", "https://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testLabel", "", "https://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testLabel", "testDeploymentName", "", "testApiKey", "testApiVersion")]
    [InlineData("testLabel", "testDeploymentName", "https://testEndpoint.com", "", "testApiVersion")]
    public void ConstructorWithEmptyParametersThrowsValidationException(
        string label, string deploymentName, string endpoint, string apiKey, string apiVersion)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion));
        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    [Theory]
    [InlineData("testLabel", "testDeploymentName", "http://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testLabel", "testDeploymentName", "testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testLabel", "testDeploymentName", "testEndpoint", "testApiKey", "testApiVersion")]
    public void ConstructorWithMissingPrefixParametersThrowsValidationException(
        string label, string deploymentName, string endpoint, string apiKey, string apiVersion)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion));
        Assert.Equal(ValidationException.ErrorCodes.MissingPrefix, exception?.ErrorCode);
    }

    [Fact]
    public void EndpointWithValidValueDoesNotThrow()
    {
        // Arrange
        string label = "testLabel";
        string deploymentName = "testDeploymentName";
        string endpoint = "https://testEndpoint.com";
        string apiKey = "testApiKey";
        string apiVersion = "testApiVersion";

        // Act
        var config = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        // Assert
        Assert.Equal(endpoint, config.Endpoint);
    }
}
