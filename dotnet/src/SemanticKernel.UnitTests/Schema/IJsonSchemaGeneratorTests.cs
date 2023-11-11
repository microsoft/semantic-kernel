// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Prompt;
using Xunit;

namespace SemanticKernel.UnitTests.Schema;

/// <summary>
/// Unit tests of <see cref="IJsonSchemaGenerator"/>.
/// </summary>
public sealed class IJsonSchemaGeneratorTests
{
    [Fact]
    public void ShouldUseDefaultJsonSchemaGenerator()
    {
        // Arrange
        // Act
        var schema = JsonSchemaGenerator.GenerateSchema(typeof(PromptNode), "description");

        // Assert
        Assert.NotNull(schema);
        Assert.Equal("object", schema.RootElement.GetProperty("type").GetString());
    }
}
