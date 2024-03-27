// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class VertexAIGeminiChatCompletionServiceTests
{
    [Fact]
    public void AttributesShouldContainModelIdBearerAsString()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new VertexAIGeminiChatCompletionService(model, "key", "location", "project");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsFunc()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new VertexAIGeminiChatCompletionService(model, () => Task.FromResult("key"), "location", "project");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
