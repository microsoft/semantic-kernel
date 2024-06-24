// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
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
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"object\" }")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItInfersSchemaFromType()
    {
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(int) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"number\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(double) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"string\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(string) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"boolean\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(bool) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"object\" }")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(object) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"array\",\"items\":{\"type\":\"boolean\"}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(bool[]) }.Schema));
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":\"string\"},\"Value2\":{\"type\":\"integer\"},\"Value3\":{\"type\":\"number\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
    }

    [Fact]
    public void ItCantInferSchemaFromUnsupportedType()
    {
        Assert.Null(new KernelParameterMetadata("p") { ParameterType = typeof(void) }.Schema);
        Assert.Null(new KernelParameterMetadata("p") { ParameterType = typeof(int*) }.Schema);
    }

    [Fact]
    public void ItIncludesDescriptionInSchema()
    {
        var m = new KernelParameterMetadata("p") { Description = "something neat", ParameterType = typeof(int) };
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\", \"description\":\"something neat\" }")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItIncludesDefaultValueInSchema()
    {
        var m = new KernelParameterMetadata("p") { DefaultValue = "42", ParameterType = typeof(int) };
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\", \"description\":\"(default value: 42)\" }")), JsonSerializer.Serialize(m.Schema));
    }

    [Fact]
    public void ItIncludesDescriptionAndDefaultValueInSchema()
    {
        var m = new KernelParameterMetadata("p") { Description = "something neat", DefaultValue = "42", ParameterType = typeof(int) };
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"integer\", \"description\":\"something neat (default value: 42)\" }")), JsonSerializer.Serialize(m.Schema));
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

#pragma warning disable CS0649 // fields never assigned to
#pragma warning disable CA1812 // class never instantiated
    internal sealed class Example
    {
        public string? Value1;
        public int Value2;
        public double Value3;
    }
#pragma warning restore CA1812
#pragma warning restore CS0649
}
