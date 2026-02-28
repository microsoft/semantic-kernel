// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelJsonSchemaTests
{
    [Fact]
    public void ItParsesJsonSchemaSuccessfully()
    {
        const string ValidJsonSchema = """
            {
              "$schema": "http://json-schema.org/draft-07/schema#",
              "type": "object",
              "properties": {
                "title": {
                  "type": "string",
                  "description": "The title of the book"
                },
                "author": {
                  "type": "string",
                  "description": "The name of the author"
                },
                "year": {
                  "type": "integer",
                  "description": "The year of publication",
                  "minimum": 0
                },
                "genre": {
                  "type": "string",
                  "description": "The genre of the book",
                  "enum": ["fiction", "non-fiction", "biography", "poetry", "other"]
                },
                "pages": {
                  "type": "integer",
                  "description": "The number of pages in the book",
                  "minimum": 1
                },
                "rating": {
                  "type": "number",
                  "description": "The average rating of the book",
                  "minimum": 0,
                  "maximum": 5
                }
              },
              "required": ["title", "author", "year", "genre", "pages", "rating"]
            }
            """;

        KernelJsonSchema schema1 = KernelJsonSchema.Parse(ValidJsonSchema);
        KernelJsonSchema schema2 = KernelJsonSchema.Parse((ReadOnlySpan<char>)ValidJsonSchema);
        KernelJsonSchema schema3 = KernelJsonSchema.Parse(Encoding.UTF8.GetBytes(ValidJsonSchema));

        string expected = JsonSerializer.Serialize(JsonElement.Parse(ValidJsonSchema)); // roundtrip through JsonSerializer to normalize whitespace

        foreach (KernelJsonSchema schema in new[] { schema1, schema2, schema3 })
        {
            Assert.Equal(expected, JsonSerializer.Serialize(schema.RootElement));
            Assert.Equal(expected, JsonSerializer.Serialize(JsonElement.Parse(schema.ToString())));
        }
    }

    [Fact]
    public void ItThrowsOnInvalidJson()
    {
        const string InvalidJsonSchema = """
            {
              "$schema": "http://json-schema.org/draft-07/schema#",
              "type":,
              "properties": {
                "title": {
                  "type": "string",
                  "description": "The title of the book"
                },
            }
            """;

        Assert.Throws<ArgumentNullException>(() => KernelJsonSchema.Parse((string)null!));

        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse(string.Empty));
        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse(ReadOnlySpan<char>.Empty));
        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse(ReadOnlySpan<byte>.Empty));

        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse(InvalidJsonSchema));
        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse((ReadOnlySpan<char>)InvalidJsonSchema));
        Assert.ThrowsAny<JsonException>(() => KernelJsonSchema.Parse(Encoding.UTF8.GetBytes(InvalidJsonSchema)));
    }

    [Fact]
    public void ItShouldExcludeReadOnlyPropertiesFromSchema()
    {
        var function = KernelFunctionFactory.CreateFromMethod(
            (MyComplexType input) => { },
            "TestFunction");

        var schema = function.Metadata.Parameters[0].Schema;
        var jsonSchemaString = schema?.ToString();

        Assert.NotNull(jsonSchemaString);
        Assert.Contains("Status", jsonSchemaString); 
        Assert.DoesNotContain("Derived", jsonSchemaString); 
    }

    /// <summary>
    /// A helper class specific to this test case.
    /// Used to verify that read-only properties are ignored by the schema generator.
    /// </summary>
    private class MyComplexType
    {
        [Description("The current status of the user account")]
        public MyStatus Status { get; set; }

        public string Derived => $"Status is {Status}";
    }

    private enum MyStatus
    {
        Active,
        Inactive
    }

    // TODO: KernelJsonSchema currently validates that the input is valid JSON but not that it's valid JSON schema.
    //[Theory]
    //[InlineData("{ \"type\":\"invalid\" }")]
    //public void ItThrowsOnInvalidJsonSchema(string invalidSchema)
    //{
    //    Assert.Throws<JsonException>(() => KernelJsonSchema.Parse(invalidSchema));
    //    Assert.Throws<JsonException>(() => KernelJsonSchema.Parse((ReadOnlySpan<char>)invalidSchema));
    //    Assert.Throws<JsonException>(() => KernelJsonSchema.Parse(Encoding.UTF8.GetBytes(invalidSchema)));
    //}
}
