// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="OpenAIConfig"/>
/// </summary>
public class OpenAIConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string serviceId = "testId";
        string modelId = "testModelId";
        string apiKey = "testApiKey";
        string orgId = "testOrgId";

        // Act
        var config = new OpenAIConfig(serviceId, modelId, apiKey, orgId);

        // Assert
        Assert.Equal(serviceId, config.ServiceId);
        Assert.Equal(modelId, config.ModelId);
        Assert.Equal(apiKey, config.APIKey);
        Assert.Equal(orgId, config.OrgId);
    }

    [Theory]
    [InlineData("", "testModelId", "testApiKey", "testOrgId")]
    [InlineData("testId", "", "testApiKey", "testOrgId")]
    [InlineData("testId", "testModelId", "", "testOrgId")]
    public void ConstructorWithEmptyRequiredParameterThrowsArgumentException(
        string serviceId, string modelId, string apiKey, string orgId)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new OpenAIConfig(serviceId, modelId, apiKey, orgId));

        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    [Fact]
    public void OrgIdWithNullValueDoesNotThrow()
    {
        // Arrange
        string serviceId = "testId";
        string modelId = "testModelId";
        string apiKey = "testApiKey";

        // Act
        var config = new OpenAIConfig(serviceId, modelId, apiKey, null);

        // Assert
        Assert.Null(config.OrgId);
    }
}
