#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.TextEmbedding;

public sealed class GoogleAIGeminiTextEmbeddingGenerationServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new GoogleAIGeminiTextEmbeddingGenerationService(model, "key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
