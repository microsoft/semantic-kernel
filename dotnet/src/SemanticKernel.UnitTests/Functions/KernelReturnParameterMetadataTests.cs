// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously

namespace SemanticKernel.UnitTests.Functions;

public class KernelReturnParameterMetadataTests
{
    [Fact]
    public void ItRoundtripsArguments()
    {
        var m = new KernelReturnParameterMetadata { Description = "something", ParameterType = typeof(int), Schema = KernelJsonSchema.Parse("""{ "type":"object" }""") };
        Assert.Equal("something", m.Description);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"object" }""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItInfersSchemaFromType()
    {
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"integer" }""")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(int) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"number" }""")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(double) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"string" }""")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(string) }.Schema));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDescriptionInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelReturnParameterMetadata(jsos) { Description = "d", ParameterType = typeof(int) } :
            new KernelReturnParameterMetadata() { Description = "d", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"d", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItCachesInferredSchemas()
    {
        var m = new KernelReturnParameterMetadata { ParameterType = typeof(KernelParameterMetadataTests.Example) };
        Assert.Same(m.Schema, m.Schema);
    }

    [Fact]
    public void ItCopiesInferredSchemaToCopy()
    {
        var m = new KernelReturnParameterMetadata { ParameterType = typeof(KernelParameterMetadataTests.Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelReturnParameterMetadata(m);
        Assert.Same(schema1, m.Schema);
    }

    [Fact]
    public void ItInvalidatesSchemaForNewType()
    {
        var m = new KernelReturnParameterMetadata { ParameterType = typeof(KernelParameterMetadataTests.Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelReturnParameterMetadata(m) { ParameterType = typeof(int) };
        Assert.NotNull(m.Schema);
        Assert.NotSame(schema1, m.Schema);
    }

    [Fact]
    public void ItInvalidatesSchemaForNewDescription()
    {
        var m = new KernelReturnParameterMetadata { ParameterType = typeof(KernelParameterMetadataTests.Example) };
        KernelJsonSchema? schema1 = m.Schema;
        Assert.NotNull(schema1);

        m = new KernelReturnParameterMetadata(m) { Description = "something new" };
        Assert.NotNull(m.Schema);
        Assert.NotSame(schema1, m.Schema);
    }

    [Fact]
    public void ItRepresentsUnderlyingType()
    {
        Assert.Equal(typeof(void), KernelFunctionFactory.CreateFromMethod(() => { }).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(() => 42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(string), KernelFunctionFactory.CreateFromMethod(() => "42").Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(bool), KernelFunctionFactory.CreateFromMethod(() => true).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(() => (int?)42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(async () => 42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(async ValueTask<int> () => 42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(async () => (int?)42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(int), KernelFunctionFactory.CreateFromMethod(async ValueTask<int?> () => (int?)42).Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(string), KernelFunctionFactory.CreateFromMethod(async () => "42").Metadata.ReturnParameter.ParameterType);
        Assert.Equal(typeof(string), KernelFunctionFactory.CreateFromMethod(async ValueTask<string> () => "42").Metadata.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanBeConstructedWithAllParameters()
    {
        // Test the new constructor that accepts all parameters
        var schema = KernelJsonSchema.Parse("""{ "type": "string", "description": "test return schema" }""");
        var m = new KernelReturnParameterMetadata(
            description: "Return parameter description",
            parameterType: typeof(string),
            schema: schema);

        Assert.Equal("Return parameter description", m.Description);
        Assert.Equal(typeof(string), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(schema), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItCanBeConstructedWithAllParametersAndJsonSerializerOptions()
    {
        // Test the new constructor with JsonSerializerOptions
        var jsos = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        var schema = KernelJsonSchema.Parse("""{ "type": "integer" }""");
        var m = new KernelReturnParameterMetadata(
            description: "Return parameter",
            parameterType: typeof(int),
            schema: schema,
            jsonSerializerOptions: jsos);

        Assert.Equal("Return parameter", m.Description);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(schema), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItUsesDefaultValuesInNewConstructor()
    {
        // Test that optional parameters have correct default values
        var m = new KernelReturnParameterMetadata();

        Assert.Empty(m.Description);
        Assert.Null(m.ParameterType);
        Assert.Null(m.Schema);
    }

    [Fact]
    public void ItInfersSchemaWhenNotProvidedInNewConstructor()
    {
        // Test that schema is inferred from type when not explicitly provided
        var m = new KernelReturnParameterMetadata(
            description: "An integer return parameter",
            parameterType: typeof(int));

        Assert.NotNull(m.Schema);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"An integer return parameter", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItHandlesNullDescriptionInNewConstructor()
    {
        // Test that null description is handled correctly
        var m = new KernelReturnParameterMetadata(
            description: null,
            parameterType: typeof(string));

        Assert.Empty(m.Description); // null description should become empty string
        Assert.Equal(typeof(string), m.ParameterType);
    }

    [Fact]
    public void ItHandlesNullSchemaInNewConstructor()
    {
        // Test that null schema parameter is handled correctly
        var m = new KernelReturnParameterMetadata(
            description: "Test return param",
            parameterType: typeof(string),
            schema: null);

        Assert.Equal("Test return param", m.Description);
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
            new KernelReturnParameterMetadata(
                description: "Test return parameter",
                parameterType: typeof(int),
                jsonSerializerOptions: jsos) :
            new KernelReturnParameterMetadata(
                description: "Test return parameter",
                parameterType: typeof(int));

        Assert.Equal("Test return parameter", m.Description);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"description":"Test return parameter", "type":"integer"}""")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItHandlesOnlyDescriptionInNewConstructor()
    {
        // Test constructor with only description parameter
        var m = new KernelReturnParameterMetadata(description: "Only description provided");

        Assert.Equal("Only description provided", m.Description);
        Assert.Null(m.ParameterType);
        Assert.Null(m.Schema);
    }

    [Fact]
    public void ItHandlesOnlyParameterTypeInNewConstructor()
    {
        // Test constructor with only parameter type
        var m = new KernelReturnParameterMetadata(parameterType: typeof(bool));

        Assert.Empty(m.Description);
        Assert.Equal(typeof(bool), m.ParameterType);
        Assert.NotNull(m.Schema);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{"type":"boolean"}""")), JsonSerializer.Serialize(m.Schema));
    }
}
