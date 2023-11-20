// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class SKJsonSchemaTests
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

        SKJsonSchema schema1 = SKJsonSchema.Parse(ValidJsonSchema);
        SKJsonSchema schema2 = SKJsonSchema.Parse((ReadOnlySpan<char>)ValidJsonSchema);
        SKJsonSchema schema3 = SKJsonSchema.Parse(Encoding.UTF8.GetBytes(ValidJsonSchema));

        string expected = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(ValidJsonSchema)); // roundtrip through JsonSerializer to normalize whitespace

        foreach (SKJsonSchema schema in new[] { schema1, schema2, schema3 })
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

        Assert.Throws<ArgumentNullException>(() => SKJsonSchema.Parse((string)null!));

        Assert.Throws<JsonException>(() => SKJsonSchema.Parse(string.Empty));
        Assert.Throws<JsonException>(() => SKJsonSchema.Parse(ReadOnlySpan<char>.Empty));
        Assert.Throws<JsonException>(() => SKJsonSchema.Parse(ReadOnlySpan<byte>.Empty));

        Assert.Throws<JsonException>(() => SKJsonSchema.Parse(InvalidJsonSchema));
        Assert.Throws<JsonException>(() => SKJsonSchema.Parse((ReadOnlySpan<char>)InvalidJsonSchema));
        Assert.Throws<JsonException>(() => SKJsonSchema.Parse(Encoding.UTF8.GetBytes(InvalidJsonSchema)));
    }
}
