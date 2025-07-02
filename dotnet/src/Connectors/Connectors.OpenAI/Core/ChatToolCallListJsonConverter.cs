// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// JSON converter for IReadOnlyList&lt;ChatToolCall&gt; that handles serialization and deserialization
/// of ChatToolCall objects using their basic properties.
/// </summary>
internal sealed class ChatToolCallListJsonConverter : JsonConverter<IReadOnlyList<ChatToolCall>>
{
    public override IReadOnlyList<ChatToolCall> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType == JsonTokenType.Null)
        {
            return [];
        }

        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException("Expected array for ChatToolCall list");
        }

        var toolCalls = new List<ChatToolCall>();

        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndArray)
            {
                break;
            }

            if (reader.TokenType == JsonTokenType.StartObject)
            {
                var toolCall = ReadChatToolCall(ref reader);
                if (toolCall != null)
                {
                    toolCalls.Add(toolCall);
                }
            }
        }

        return toolCalls;
    }

    public override void Write(Utf8JsonWriter writer, IReadOnlyList<ChatToolCall> value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();

        foreach (var toolCall in value)
        {
            WriteChatToolCall(writer, toolCall);
        }

        writer.WriteEndArray();
    }

    private static ChatToolCall? ReadChatToolCall(ref Utf8JsonReader reader)
    {
        string? id = null;
        string? functionName = null;
        string? arguments = null;

        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndObject)
            {
                break;
            }

            if (reader.TokenType == JsonTokenType.PropertyName)
            {
                var propertyName = reader.GetString();
                reader.Read();

                switch (propertyName)
                {
                    case "Id":
                        id = reader.GetString();
                        break;
                    case "FunctionName":
                        functionName = reader.GetString();
                        break;
                    case "FunctionArguments":
                        arguments = reader.GetString();
                        break;
                }
            }
        }

        if (id != null && functionName != null && arguments != null)
        {
            return ChatToolCall.CreateFunctionToolCall(id, functionName, BinaryData.FromString(arguments));
        }

        return null;
    }

    private static void WriteChatToolCall(Utf8JsonWriter writer, ChatToolCall toolCall)
    {
        writer.WriteStartObject();
        writer.WriteString("Id", toolCall.Id);
        writer.WriteString("FunctionName", toolCall.FunctionName);
        writer.WriteString("FunctionArguments", toolCall.FunctionArguments.ToString());
        writer.WriteEndObject();
    }
}
