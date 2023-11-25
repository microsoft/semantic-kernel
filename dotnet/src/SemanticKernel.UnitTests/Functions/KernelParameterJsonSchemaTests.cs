// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelParameterJsonSchemaTests
{
    [Fact]
    public void ItParsesJsonSchemaSuccessfully()
    {
        const string ValidJsonSchema = @"
{
  ""$schema"": ""http://json-schema.org/draft-07/schema#"",
  ""type"": ""object"",
  ""properties"": {
    ""title"": {
      ""type"": ""string"",
      ""description"": ""The title of the book""
    },
    ""author"": {
      ""type"": ""string"",
      ""description"": ""The name of the author""
    },
    ""year"": {
      ""type"": ""integer"",
      ""description"": ""The year of publication"",
      ""minimum"": 0
    },
    ""genre"": {
      ""type"": ""string"",
      ""description"": ""The genre of the book"",
      ""enum"": [""fiction"", ""non-fiction"", ""biography"", ""poetry"", ""other""]
    },
    ""pages"": {
      ""type"": ""integer"",
      ""description"": ""The number of pages in the book"",
      ""minimum"": 1
    },
    ""rating"": {
      ""type"": ""number"",
      ""description"": ""The average rating of the book"",
      ""minimum"": 0,
      ""maximum"": 5
    }
  },
  ""required"": [""title"", ""author"", ""year"", ""genre"", ""pages"", ""rating""]
}";

        KernelParameterJsonSchema schema1 = KernelParameterJsonSchema.Parse(ValidJsonSchema);
        KernelParameterJsonSchema schema2 = KernelParameterJsonSchema.Parse((ReadOnlySpan<char>)ValidJsonSchema);
        KernelParameterJsonSchema schema3 = KernelParameterJsonSchema.Parse(Encoding.UTF8.GetBytes(ValidJsonSchema));

        string expected = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(ValidJsonSchema)); // roundtrip through JsonSerializer to normalize whitespace

        foreach (KernelParameterJsonSchema schema in new[] { schema1, schema2, schema3 })
        {
            Assert.Equal(expected, JsonSerializer.Serialize(schema.RootElement));
            Assert.Equal(expected, JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(schema.ToString())));
        }
    }

    [Fact]
    public void ItThrowsOnInvalidJsonSchema()
    {
        const string InvalidJsonSchema = @"
{
  ""$schema"": ""http://json-schema.org/draft-07/schema#"",
  ""type"":,
  ""properties"": {
    ""title"": {
      ""type"": ""string"",
      ""description"": ""The title of the book""
    },
}";

        Assert.Throws<ArgumentNullException>(() => KernelParameterJsonSchema.Parse((string)null!));

        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse(string.Empty));
        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse(ReadOnlySpan<char>.Empty));
        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse(ReadOnlySpan<byte>.Empty));

        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse(InvalidJsonSchema));
        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse((ReadOnlySpan<char>)InvalidJsonSchema));
        Assert.Throws<JsonException>(() => KernelParameterJsonSchema.Parse(Encoding.UTF8.GetBytes(InvalidJsonSchema)));
    }
}
