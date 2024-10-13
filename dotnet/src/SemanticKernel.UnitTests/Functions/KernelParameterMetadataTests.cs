<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

using System;
using System.ComponentModel;
using System.Text.Json;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using Json.Schema.Generation;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Json.Schema.Generation;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
using Json.Schema.Generation;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using Json.Schema.Generation;
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":\"string\"},\"Value2\":{\"type\":\"integer\"},\"Value3\":{\"type\":\"number\", \"description\":\"This is the Value3 field.\"},\"Value4\":{\"type\":\"number\", \"description\":\"This is the Value4 property.\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":\"string\"},\"Value2\":{\"type\":\"integer\"},\"Value3\":{\"type\":\"number\", \"description\":\"This is the Value3 field.\"},\"Value4\":{\"type\":\"number\", \"description\":\"This is the Value4 property.\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":\"string\"},\"Value2\":{\"type\":\"integer\"},\"Value3\":{\"type\":\"number\", \"description\":\"This is the Value3 field.\"},\"Value4\":{\"type\":\"number\", \"description\":\"This is the Value4 property.\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("{\"type\":\"object\",\"properties\":{\"Value1\":{\"type\":\"string\"},\"Value2\":{\"type\":\"integer\"},\"Value3\":{\"type\":\"number\", \"description\":\"This is the Value3 field.\"},\"Value4\":{\"type\":\"number\", \"description\":\"This is the Value4 property.\"}}}")), JsonSerializer.Serialize(new KernelParameterMetadata("p") { ParameterType = typeof(Example) }.Schema));
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"integer", "description":"something neat" }""")), JsonSerializer.Serialize(m.Schema));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDefaultValueInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelParameterMetadata("p", jsos) { DefaultValue = "42", ParameterType = typeof(int) } :
            new KernelParameterMetadata("p") { DefaultValue = "42", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"integer", "description":"(default value: 42)" }""")), JsonSerializer.Serialize(m.Schema));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForPrimitives))]
    public void ItIncludesDescriptionAndDefaultValueInSchema(JsonSerializerOptions? jsos)
    {
        var m = jsos is not null ?
            new KernelParameterMetadata("p", jsos) { Description = "something neat", DefaultValue = "42", ParameterType = typeof(int) } :
            new KernelParameterMetadata("p") { Description = "something neat", DefaultValue = "42", ParameterType = typeof(int) };

        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"integer", "description":"something neat (default value: 42)" }""")), JsonSerializer.Serialize(m.Schema));
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

#pragma warning disable CA1812 // class never instantiated
    internal sealed class Example
    {
        public string? Value1 { get; set; }
        [Description("Some property that does something.")]
        public int Value2 { get; set; }
        [Description("This one also does something.")]
        public double Value3 { get; set; }
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        public string? Value1;
        public int Value2;
        [System.ComponentModel.Description("This is the Value3 field.")]
        public double Value3;
        [System.ComponentModel.Description("This is the Value4 property.")]
        public double Value4 { get; set; }
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    }
#pragma warning restore CA1812
}
