// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Services;

public sealed class GoogleAITextEmbeddingGenerationServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new GoogleAITextEmbeddingGenerationService(model, "key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
