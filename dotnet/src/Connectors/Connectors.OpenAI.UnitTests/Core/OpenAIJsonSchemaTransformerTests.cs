// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for schema transformations used by OpenAI clients.
/// </summary>
public sealed class OpenAIJsonSchemaTransformerTests
{
    private static readonly AIJsonSchemaCreateOptions s_jsonSchemaCreateOptions = new()
    {
        TransformOptions = new()
        {
            DisallowAdditionalProperties = true,
            RequireAllProperties = true,
            MoveDefaultKeywordToDescription = true,
        }
    };

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        WriteIndented = false
    };

    [Fact]
    public void ItTransformsJsonSchemaCorrectly()
    {
        // Arrange
        var type = typeof(Parent);
        var expectedSchema = """
            {
              "type": "object",
              "properties": {
                "Items": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "NumericProperty": {
                        "description": "Description of numeric property.",
                        "type": "integer"
                      }
                    },
                    "additionalProperties": false,
                    "required": [
                      "NumericProperty"
                    ]
                  }
                },
                "Item": {
                  "type": "object",
                  "properties": {
                    "NumericProperty": {
                      "description": "Description of numeric property.",
                      "type": "integer"
                    }
                  },
                  "additionalProperties": false,
                  "required": [
                    "NumericProperty"
                  ]
                },
                "NullableItems": {
                  "type": [
                    "array",
                    "null"
                  ],
                  "items": {
                    "type": ["object","null"],
                    "properties": {
                      "TextProperty": {
                        "type": [
                          "string",
                          "null"
                        ]
                      }
                    },
                    "additionalProperties": false,
                    "required": [
                      "TextProperty"
                    ]
                  }
                },
                "NullableItem": {
                  "type": [
                    "object",
                    "null"
                  ],
                  "properties": {
                    "TextProperty": {
                      "type": [
                        "string",
                        "null"
                      ]
                    }
                  },
                  "additionalProperties": false,
                  "required": [
                    "TextProperty"
                  ]
                },
                "TextProperty": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              },
              "additionalProperties": false,
              "required": [
                "Items",
                "Item",
                "NullableItems",
                "NullableItem",
                "TextProperty"
              ]
            }
            """;

        // Act
        var schema = KernelJsonSchemaBuilder.Build(type, configuration: s_jsonSchemaCreateOptions);

        // Assert
        Assert.Equal(NormalizeJson(expectedSchema), NormalizeJson(schema.ToString()));
    }

    #region private

    private static string NormalizeJson(string json)
    {
        using JsonDocument doc = JsonDocument.Parse(json);
        return JsonSerializer.Serialize(doc, s_jsonSerializerOptions);
    }

    private sealed class Parent
    {
        public List<Child> Items { get; set; } = [];

        public Child Item { get; set; } = new();

        public List<ChildNullable?>? NullableItems { get; set; }

        public ChildNullable? NullableItem { get; set; }

        public string? TextProperty { get; set; }
    }

    private sealed class Child
    {
        [Description("Description of numeric property.")]
        public int NumericProperty { get; set; }
    }

    private struct ChildNullable
    {
        public string? TextProperty { get; set; }
    }

    #endregion
}
