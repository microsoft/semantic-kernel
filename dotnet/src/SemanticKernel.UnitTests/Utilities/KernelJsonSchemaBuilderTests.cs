// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public class KernelJsonSchemaBuilderTests
{
    [Fact]
    public void ItShouldBuildJsonSchemaForTypesWithPublicMembersHavingTypesThatCanRepresentOtherTypesWithDefaultValuesInTheConstructor()
    {
        // Arrange & Act
        var schema = KernelJsonSchemaBuilder.Build(typeof(ClassWithDefaultValuesInConstructorForTypesThatCanRepresentOtherTypes));

        // Assert
        Assert.NotNull(schema?.RootElement);
    }

#pragma warning disable CA1812 // Instantiated by reflection
    private sealed class ClassWithDefaultValuesInConstructorForTypesThatCanRepresentOtherTypes
    {
        public ClassWithDefaultValuesInConstructorForTypesThatCanRepresentOtherTypes(object? content = null, KernelJsonSchema? schema = null)
        {
            this.Content = content;
            this.Schema = schema;
        }

        public object? Content { get; set; }

        public KernelJsonSchema? Schema { get; set; }
    }
#pragma warning restore CA1812 // Instantiated by reflection
}
