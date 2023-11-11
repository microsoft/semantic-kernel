// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Functions.JsonSchema;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.JsonSchema;

public sealed class FunctionsJsonSchemaGeneratorTests
{
    [Fact]
    public void ItShouldGenerateSchema()
    {
        // Arrange
        var jsonSchemaGenerator = new FunctionsJsonSchemaGenerator();

        // Act
        var schema = jsonSchemaGenerator.GenerateSchema(typeof(SampleModel), "description");

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
