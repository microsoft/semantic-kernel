// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Services;

public sealed class AnthropicChatCompletionServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new AnthropicChatCompletionService(model, "key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
