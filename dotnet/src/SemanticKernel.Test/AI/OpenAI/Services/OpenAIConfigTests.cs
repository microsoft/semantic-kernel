// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernelTests.AI.OpenAI.Services;

/// <summary>
/// Unit tests of <see cref="OpenAIConfig"/>
/// </summary>
public class OpenAIConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string label = "testLabel";
        string modelId = "testModelId";
        string apiKey = "testApiKey";
        string orgId = "testOrgId";

        // Act
        var config = new OpenAIConfig(label, modelId, apiKey, orgId);

        // Assert
        Assert.Equal(label, config.Label);
        Assert.Equal(modelId, config.ModelId);
        Assert.Equal(apiKey, config.APIKey);
        Assert.Equal(orgId, config.OrgId);
    }

    [Theory]
    [InlineData("", "testModelId", "testApiKey", "testOrgId")]
    [InlineData("testLabel", "", "testApiKey", "testOrgId")]
    [InlineData("testLabel", "testModelId", "", "testOrgId")]
    public void ConstructorWithEmptyRequiredParameterThrowsArgumentException(
        string label, string modelId, string apiKey, string orgId)
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new OpenAIConfig(label, modelId, apiKey, orgId));

        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    [Fact]
    public void OrgIdWithNullValueDoesNotThrow()
    {
        // Arrange
        string label = "testLabel";
        string modelId = "testModelId";
        string apiKey = "testApiKey";

        // Act
        var config = new OpenAIConfig(label, modelId, apiKey, null);

        // Assert
        Assert.Null(config.OrgId);
    }
}
