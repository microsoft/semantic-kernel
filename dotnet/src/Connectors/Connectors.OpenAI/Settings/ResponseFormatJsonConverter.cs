// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Text.Json;
using System.Text.Json.Serialization;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// JSON converter for <see cref="OpenAIPromptExecutionSettings.ResponseFormat"/> that writes <see cref="Type"/> and
/// <see cref="ChatResponseFormat"/> values in a form that can be deserialized without losing the requested response format.
/// </summary>
internal sealed class ResponseFormatJsonConverter : JsonConverter<object>
{
    /// <inheritdoc/>
    public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        // Keep the default object deserialization (a JsonElement), which ClientCore and ToChatOptions already understand.
        // Never resolve a Type from the payload: loading type names from serialized data would be a deserialization vulnerability.
        return JsonSerializer.Deserialize<object>(ref reader, options);
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
    {
        switch (value)
        {
            case Type formatObjectType:
                WriteChatResponseFormat(writer, OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(formatObjectType));
                break;

            case ChatResponseFormat chatResponseFormat:
                WriteChatResponseFormat(writer, chatResponseFormat);
                break;

            default:
                // Strings, JsonElement and any other values keep the default object serialization.
                JsonSerializer.Serialize<object>(writer, value, options);
                break;
        }
    }

    private static void WriteChatResponseFormat(Utf8JsonWriter writer, ChatResponseFormat chatResponseFormat)
    {
        // Use the OpenAI wire representation so that a deserialized value produces the same request payload.
        // System.Text.Json cannot serialize ChatResponseFormat itself and would write an empty object.
        using JsonDocument document = JsonDocument.Parse(ModelReaderWriter.Write(chatResponseFormat).ToMemory());
        JsonElement responseFormat = document.RootElement;

        // Text and JSON object formats are written as the plain strings that ClientCore and ToChatOptions map back,
        // because both treat any JSON object response format as a JSON schema.
        if (responseFormat.ValueKind == JsonValueKind.Object &&
            responseFormat.TryGetProperty("type", out JsonElement type) &&
            type.ValueKind == JsonValueKind.String &&
            type.GetString() is "text" or "json_object")
        {
            writer.WriteStringValue(type.GetString());
            return;
        }

        responseFormat.WriteTo(writer);
    }
}
