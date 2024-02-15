// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously

namespace SemanticKernel.UnitTests.Functions;

public class KernelReturnParameterMetadataTests
{
    [Fact]
    public void ItRoundtripsArguments()
    {
        var m = new KernelReturnParameterMetadata { Description = "something", ParameterType = typeof(int), Schema = KernelJsonSchema.Parse("{ \"type\":\"object\" }") };
        Assert.Equal("something", m.Description);
        Assert.Equal(typeof(int), m.ParameterType);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"object\" }")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItInfersSchemaFromType()
    {
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\" }")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(int) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"number\" }")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(double) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"string\" }")), JsonSerializer.Serialize(new KernelReturnParameterMetadata { ParameterType = typeof(string) }.Schema)); ;
    }

    [Fact]
    public void ItIncludesDescriptionInSchema()
    {
        var m = new KernelReturnParameterMetadata { Description = "d", ParameterType = typeof(int) };
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\", \"description\":\"d\" }")), JsonSerializer.Serialize(m.Schema));
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
}
