// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelParameterMetadataTests
{
    [Fact]
    public void ItThrowsForInvalidName()
    {
        Assert.Throws<ArgumentNullException>(() => new KernelParameterMetadata((string)null!));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata(""));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata("     "));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata("\t\r\v "));
    }

    [Fact]
    public void ItCanBeConstructedWithJustName()
    {
        var m = new KernelParameterMetadata("p");
        Assert.Equal("p", m.Name);
        Assert.Empty(m.Description);
        Assert.Null(m.ParameterType);
        Assert.Null(m.Schema);
        Assert.Null(m.DefaultValue);
        Assert.False(m.IsRequired);
    }

    [Fact]
    public void ItRoundtripsArguments()
    {
        var m = new KernelParameterMetadata("p") { Description = "d", DefaultValue = "v", IsRequired = true, ParameterType = typeof(int), Schema = KernelJsonSchema.Parse("{ \"type\":\"object\" }") };
        Assert.Equal("p", m.Name);
        Assert.Equal("d", m.Description);
        Assert.Equal("v", m.DefaultValue);
        Assert.True(m.IsRequired);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"object" }""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItInfersSchemaFromType()
    {
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(int) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"number\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(double) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"string\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(string) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"boolean\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(bool) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(object) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"array\",\"items\":{\"type\":\"boolean\"}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(bool[]) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":[\"string\",\"null\"]},\"Value2\":{\"description\":\"Some property that does something.\",\"type\":\"integer\"},\"Value3\":{\"description\":\"This one also does something.\",\"type\":\"number\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
    }

    [Fact]
    public void ItCantInferSchemaFromUnsupportedType()
    {
        Assert.Null(new KernelParameterMetadata("p") { ParameterType = typeof(void) }.Schema);
        Assert.Null(new KernelParameterMetadata("p") { ParameterType = typeof(int*) }.Schema);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDescriptionInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelParameterMetadata("p", jsos) { Description = "something neat", ParameterType = typeof(int) } :
            new KernelParameterMetadata("p") { Description = "something neat", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"something neat", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDefaultValueInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelParameterMetadata("p", jsos) { DefaultValue = "42", ParameterType = typeof(int) } :
            new KernelParameterMetadata("p") { DefaultValue = "42", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"(default value: 42)", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDescriptionAndDefaultValueInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelParameterMetadata("p", jsos) { Description = "something neat", DefaultValue = "42", ParameterType = typeof(int) } :
            new KernelParameterMetadata("p") { Description = "something neat", DefaultValue = "42", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"something neat (default value: 42)", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItCachesInferredSchemas()
    {
        var m = new KernelParameterMetadata("p") { ParameterType = typeof(Example) };
        Assert.Same(m.Schema, m.Schema);
    }

    [Fact]
    public void ItCopiesInferredSchemaToCopy()
    {
        var m = new KernelParameterMetadata("p") { ParameterType = typeof(Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelParameterMetadata(m);
        Assert.Same(schema1, m.Schema);
    }

    [Fact]
    public void ItInvalidatesSchemaForNewType()
    {
        var m = new KernelParameterMetadata("p") { ParameterType = typeof(Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelParameterMetadata(m) { ParameterType = typeof(int) };
        Assert.NotNull(m.Schema);
        Assert.NotSame(schema1, m.Schema);
    }

    [Fact]
    public void ItInvalidatesSchemaForNewDescription()
    {
        var m = new KernelParameterMetadata("p") { ParameterType = typeof(Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelParameterMetadata(m) { Description = "something new" };
        Assert.NotNull(m.Schema);
        Assert.NotSame(schema1, m.Schema);
    }

    [Fact]
    public void ItInvalidatesSchemaForNewDefaultValue()
    {
        var m = new KernelParameterMetadata("p") { ParameterType = typeof(Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelParameterMetadata(m) { DefaultValue = "42" };
        Assert.NotNull(m.Schema);
        Assert.NotSame(schema1, m.Schema);
    }

    [Fact]
    public void ItCanBeConstructedWithAllParameters()
    {
        // Test the new constructor that accepts all parameters
        var schema = KernelJsonSchema.Parse("""{ "type": "string", "description": "test schema" }""");
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: "Test parameter description",
            defaultValue: "defaultVal",
            isRequired: true,
            parameterType: typeof(string),
            schema: schema);

        Assert.Equal("testParam", m.Name);
        Assert.Equal("Test parameter description", m.Description);
        Assert.Equal("defaultVal", m.DefaultValue);
        Assert.True(m.IsRequired);
        Assert.Equal(typeof(string), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(schema), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItCanBeConstructedWithAllParametersAndJsonSerializerOptions()
    {
        // Test the new constructor with JsonSerializerOptions
        var jsos = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        var schema = KernelJsonSchema.Parse("""{ "type": "integer" }""");
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: "Test parameter",
            defaultValue: 42,
            isRequired: false,
            parameterType: typeof(int),
            schema: schema,
            jsonSerializerOptions: jsos);

        Assert.Equal("testParam", m.Name);
        Assert.Equal("Test parameter", m.Description);
        Assert.Equal(42, m.DefaultValue);
        Assert.False(m.IsRequired);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(schema), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItUsesDefaultValuesInNewConstructor()
    {
        // Test that optional parameters have correct default values
        var m = new KernelParameterMetadata("testParam");

        Assert.Equal("testParam", m.Name);
        Assert.Empty(m.Description);
        Assert.Null(m.DefaultValue);
        Assert.False(m.IsRequired);
        Assert.Null(m.ParameterType);
        Assert.Null(m.Schema);
    }

    [Fact]
    public void ItThrowsForInvalidNameInNewConstructor()
    {
        // Test that the new constructor still validates the name parameter
        Assert.Throws<ArgumentNullException>(() => new KernelParameterMetadata(null!, "description"));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata("", "description"));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata("   ", "description"));
        Assert.Throws<ArgumentException>(() => new KernelParameterMetadata("\t\r\v ", "description"));
    }

    [Fact]
    public void ItInfersSchemaWhenNotProvidedInNewConstructor()
    {
        // Test that schema is inferred from type when not explicitly provided
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: "An integer parameter",
            parameterType: typeof(int));

        Assert.NotNull(m.Schema);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"An integer parameter", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItIncludesDefaultValueInInferredSchemaFromNewConstructor()
    {
        // Test that default value is included in inferred schema
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: "An integer parameter",
            defaultValue: 100,
            parameterType: typeof(int));

        Assert.NotNull(m.Schema);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"An integer parameter (default value: 100)", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItHandlesNullDescriptionInNewConstructor()
    {
        // Test that null description is handled correctly
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: null,
            defaultValue: "test",
            isRequired: true,
            parameterType: typeof(string));

        Assert.Equal("testParam", m.Name);
        Assert.Empty(m.Description); // null description should become empty string
        Assert.Equal("test", m.DefaultValue);
        Assert.True(m.IsRequired);
        Assert.Equal(typeof(string), m.ParameterType);
    }

    [Fact]
    public void ItHandlesNullSchemaInNewConstructor()
    {
        // Test that null schema parameter is handled correctly
        var m = new KernelParameterMetadata(
            name: "testParam",
            description: "Test param",
            defaultValue: null,
            isRequired: false,
            parameterType: typeof(string),
            schema: null);

        Assert.Equal("testParam", m.Name);
        Assert.Equal("Test param", m.Description);
        Assert.Null(m.DefaultValue);
        Assert.False(m.IsRequired);
        Assert.Equal(typeof(string), m.ParameterType);
        // Schema should be inferred from type since explicit schema is null
        Assert.NotNull(m.Schema);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItUsesJsonSerializerOptionsInNewConstructor(JsonSerializerOptions? jsos)
    {
        // Test that JsonSerializerOptions are used correctly in the new constructor
        var m = jsos is not null ?
            new KernelParameterMetadata(
                name: "testParam",
                description: "Test parameter",
                parameterType: typeof(int),
                jsonSerializerOptions: jsos) :
            new KernelParameterMetadata(
                name: "testParam",
                description: "Test parameter",
                parameterType: typeof(int));

        Assert.Equal("testParam", m.Name);
        Assert.Equal("Test parameter", m.Description);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"Test parameter", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

#pragma warning disable CA1812 // class never instantiated
    internal sealed class Example
    {
        public string? Value1 { get; set; }
        [Description("Some property that does something.")]
        public int Value2 { get; set; }
        [Description("This one also does something.")]
        public double Value3 { get; set; }
    }
#pragma warning restore CA1812
}
