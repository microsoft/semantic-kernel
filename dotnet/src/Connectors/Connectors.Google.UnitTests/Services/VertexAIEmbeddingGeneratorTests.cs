// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Connectors.Google;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class VertexAIEmbeddingGeneratorTests
{
    [Fact]
    public void AttributesShouldContainModelIdBearerAsString()
    {
        // Arrange & Act
        string model = "fake-model";
        using var service = new VertexAIEmbeddingGenerator(model, "key", "location", "project");

        // Assert
        Assert.Equal(model, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void AttributesShouldContainModelIdBearerAsFunc()
    {
        // Arrange & Act
        string model = "fake-model";
        using var service = new VertexAIEmbeddingGenerator(model, () => ValueTask.FromResult("key"), "location", "project");

        // Assert
        Assert.Equal(model, service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }
}
