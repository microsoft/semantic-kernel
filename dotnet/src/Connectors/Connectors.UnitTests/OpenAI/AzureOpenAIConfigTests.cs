// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

public class AzureOpenAIConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string serviceId = "testId";
        string deploymentName = "testDeploymentName";
        string endpoint = "https://testEndpoint.com";
        string apiKey = "testApiKey";
        string apiVersion = "testApiVersion";

        // Act
        var config = new AzureOpenAIConfig(serviceId, deploymentName, endpoint, apiKey, apiVersion);

        // Assert
        Assert.Equal(serviceId, config.ServiceId);
        Assert.Equal(deploymentName, config.DeploymentName);
        Assert.Equal(endpoint, config.Endpoint);
        Assert.Equal(apiKey, config.APIKey);
        Assert.Equal(apiVersion, config.APIVersion);
    }

    [Theory]
    [InlineData("", "testDeploymentName", "https://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testId", "", "https://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testId", "testDeploymentName", "", "testApiKey", "testApiVersion")]
    [InlineData("testId", "testDeploymentName", "https://testEndpoint.com", "", "testApiVersion")]
    public void ConstructorWithEmptyParametersThrowsValidationException(
        string serviceId, string deploymentName, string endpoint, string apiKey, string apiVersion)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new AzureOpenAIConfig(serviceId, deploymentName, endpoint, apiKey, apiVersion));
        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    [Theory]
    [InlineData("testId", "testDeploymentName", "http://testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testId", "testDeploymentName", "testEndpoint.com", "testApiKey", "testApiVersion")]
    [InlineData("testId", "testDeploymentName", "testEndpoint", "testApiKey", "testApiVersion")]
    public void ConstructorWithMissingPrefixParametersThrowsValidationException(
        string serviceId, string deploymentName, string endpoint, string apiKey, string apiVersion)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new AzureOpenAIConfig(serviceId, deploymentName, endpoint, apiKey, apiVersion));
        Assert.Equal(ValidationException.ErrorCodes.MissingPrefix, exception?.ErrorCode);
    }

    [Fact]
    public void EndpointWithValidValueDoesNotThrow()
    {
        // Arrange
        string serviceId = "testId";
        string deploymentName = "testDeploymentName";
        string endpoint = "https://testEndpoint.com";
        string apiKey = "testApiKey";
        string apiVersion = "testApiVersion";

        // Act
        var config = new AzureOpenAIConfig(serviceId, deploymentName, endpoint, apiKey, apiVersion);

        // Assert
        Assert.Equal(endpoint, config.Endpoint);
    }
}
