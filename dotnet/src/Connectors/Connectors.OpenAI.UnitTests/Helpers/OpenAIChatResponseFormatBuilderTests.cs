// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Helpers;

/// <summary>
/// Unit tests for <see cref="OpenAIChatResponseFormatBuilder"/> class.
/// </summary>
public sealed class OpenAIChatResponseFormatBuilderTests
{
    private readonly JsonSerializerOptions _options = new();

    public OpenAIChatResponseFormatBuilderTests()
    {
        this._options.Converters.Add(new BinaryDataJsonConverter());
    }

    [Theory]
    [MemberData(nameof(ChatResponseFormatJson))]
    public void GetJsonSchemaResponseFormatReturnsChatResponseFormatByDefault(
        string chatResponseFormatJson,
        string expectedSchemaName,
        bool? expectedStrict)
    {
        // Arrange
        var jsonDocument = JsonDocument.Parse(chatResponseFormatJson);
        var jsonElement = jsonDocument.RootElement;

        // Act
        var chatResponseFormat = OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(jsonElement);
        var (jsonSchema, schema) = this.GetResponseFormatJsonSchema(chatResponseFormat);

        // Assert
        Assert.True(jsonSchema.TryGetProperty("Name", out var name));
        Assert.True(jsonSchema.TryGetProperty("Strict", out var strict));

        Assert.Equal(expectedSchemaName, name.GetString());

        if (expectedStrict is null)
        {
            Assert.Equal(JsonValueKind.Null, strict.ValueKind);
        }
        else
        {
            Assert.Equal(expectedStrict, strict.GetBoolean());
        }

        var schemaElement = JsonDocument.Parse(schema.ToString()).RootElement;
        var nameProperty = schemaElement.GetProperty("properties").GetProperty("name");

        Assert.Equal("object", schemaElement.GetProperty("type").GetString());
        Assert.Equal("string", nameProperty.GetProperty("type").GetString());
        Assert.Equal("The person's full name", nameProperty.GetProperty("description").GetString());
    }

    [Fact]
    public void GetJsonSchemaResponseFormatThrowsExceptionWhenSchemaDoesNotExist()
    {
        // Arrange
        var json =
            """
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "Schema Name"
                }
            }
            """;

        var jsonDocument = JsonDocument.Parse(json);
        var jsonElement = jsonDocument.RootElement;

        // Act & Assert
        Assert.Throws<ArgumentException>(() => OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(jsonElement));
    }

    public static TheoryData<string, string, bool?> ChatResponseFormatJson => new()
    {
        {
            """
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The person's full name"
                    }
                }
            }
            """,
            "JsonSchema",
            null
        },
        {
            """
            {
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The person's full name"
                            }
                        }
                    }
                }
            }
            """,
            "JsonSchema",
            null
        },
        {
            """
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "Schema Name",
                    "strict": true,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The person's full name"
                            }
                        }
                    }
                }
            }
            """,
            "Schema Name",
            true
        }
    };

    #region private

    private (JsonElement JsonSchema, JsonElement JsonSchemaSchema) GetResponseFormatJsonSchema(ChatResponseFormat chatResponseFormat)
    {
        var jsonSchemaProperty = chatResponseFormat.GetType().GetProperty("JsonSchema", BindingFlags.NonPublic | BindingFlags.Instance);

        // Assert
        Assert.NotNull(jsonSchemaProperty);
        var jsonSchemaPropertyValue = jsonSchemaProperty.GetValue(chatResponseFormat);

        Assert.NotNull(jsonSchemaPropertyValue);
        var schemaProperty = jsonSchemaPropertyValue.GetType().GetProperty("Schema", BindingFlags.Public | BindingFlags.Instance);

        Assert.NotNull(schemaProperty);
        var schemaPropertyValue = schemaProperty.GetValue(jsonSchemaPropertyValue);

        Assert.NotNull(schemaPropertyValue);

        var jsonSchema = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(jsonSchemaProperty.GetValue(chatResponseFormat)));

        // Schema property gets serialized into a non-readable pattern in the jsonSchema JsonElement variable and needs to be returned separately.
        var schema = JsonSerializer.Deserialize<JsonElement>(schemaPropertyValue.ToString()!);

        return (jsonSchema, schema);
    }

    private sealed class BinaryDataJsonConverter : JsonConverter<BinaryData>
    {
        public override BinaryData Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String)
            {
                string jsonString = reader.GetString()!;
                return BinaryData.FromString(jsonString);
            }

            throw new JsonException("Expected a JSON string for BinaryData.");
        }

        public override void Write(Utf8JsonWriter writer, BinaryData value, JsonSerializerOptions options)
        {
            writer.WriteStringValue(value.ToString());
        }
    }

    #endregion
}
