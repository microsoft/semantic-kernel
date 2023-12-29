#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.TextGeneration;

public class GeminiTextGenerationServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "fake-model";
        var service = new GeminiTextGenerationService(model, "key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
