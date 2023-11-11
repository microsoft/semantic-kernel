// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Schema;
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
        var schema = JsonSchemaGenerator.GenerateSchema(typeof(SampleModel), "description");

        // Assert
        Assert.NotNull(schema);
        Assert.Equal("object", schema.RootElement.GetProperty("type").GetString());
    }

    private class SampleModel
    {
        public string? Name { get; set; }
        public string? Description { get; set; }
        public int? Age { get; set; }
    }
}
