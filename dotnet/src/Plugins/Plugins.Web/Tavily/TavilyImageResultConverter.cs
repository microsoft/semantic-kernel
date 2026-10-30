// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Reads an image result from either a plain image URL string (returned when image descriptions are not
/// requested) or an object with <c>url</c> and <c>description</c> (returned when they are).
/// </summary>
internal sealed class TavilyImageResultConverter : JsonConverter<TavilyImageResult>
{
    /// <inheritdoc />
    public override TavilyImageResult? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType == JsonTokenType.Null)
        {
            return null;
        }

        if (reader.TokenType == JsonTokenType.String)
        {
            return new TavilyImageResult(reader.GetString()!, string.Empty);
        }

        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("An image result must be a URL string or an object.");
        }

        string? url = null;
        string? description = null;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            string? name = reader.GetString();
            reader.Read();
            if (name == "url")
            {
                url = reader.TokenType == JsonTokenType.Null ? null : reader.GetString();
            }
            else if (name == "description")
            {
                description = reader.TokenType == JsonTokenType.Null ? null : reader.GetString();
            }
            else
            {
                reader.Skip();
            }
        }

        return new TavilyImageResult(
            url ?? throw new JsonException("Required property 'url' was not found in the image result."),
            description ?? throw new JsonException("Required property 'description' was not found in the image result."));
    }

    /// <inheritdoc />
    public override void Write(Utf8JsonWriter writer, TavilyImageResult value, JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WriteString("url", value.Url);
        writer.WriteString("description", value.Description);
        writer.WriteEndObject();
    }
}
