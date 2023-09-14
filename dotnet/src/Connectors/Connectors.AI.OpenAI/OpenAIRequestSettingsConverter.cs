// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// JSON converter for <see cref="OpenAIRequestSettings"/>
/// </summary>
public class OpenAIRequestSettingsConverter<T> : JsonConverter<T> where T : OpenAIRequestSettings, new()
{
    /// <inheritdoc/>
    public override T? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var requestSettings = new T();

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType == JsonTokenType.PropertyName)
            {
                string? propertyName = reader.GetString();

                reader.Read();

                switch (propertyName)
                {
                    case "temperature":
                    case "Temperature":
                        requestSettings.Temperature = reader.GetDouble();
                        break;
                    case "top_p":
                    case "TopP":
                        requestSettings.TopP = reader.GetDouble();
                        break;
                    case "frequency_penalty":
                    case "FrequencyPenalty":
                        requestSettings.FrequencyPenalty = reader.GetDouble();
                        break;
                    case "presence_penalty":
                    case "PresencePenalty":
                        requestSettings.PresencePenalty = reader.GetDouble();
                        break;
                    case "max_tokens":
                    case "MaxTokens":
                        requestSettings.MaxTokens = reader.GetInt32();
                        break;
                    case "stop_sequences":
                    case "StopSequences":
                        requestSettings.StopSequences = JsonSerializer.Deserialize<IList<string>>(ref reader, options) ?? Array.Empty<string>();
                        break;
                    case "results_per_prompt":
                    case "ResultsPerPrompt":
                        requestSettings.ResultsPerPrompt = reader.GetInt32();
                        break;
                    case "chat_system_prompt":
                    case "ChatSystemPrompt":
                        requestSettings.ChatSystemPrompt = reader.GetString() ?? OpenAIRequestSettings.DefaultChatSystemPrompt;
                        break;
                    case "token_selection_biases":
                    case "TokenSelectionBiases":
                        requestSettings.TokenSelectionBiases = JsonSerializer.Deserialize<IDictionary<int, int>>(ref reader, options) ?? new Dictionary<int, int>();
                        break;
                    case "service_id":
                    case "ServiceId":
                        requestSettings.ServiceId = reader.GetString();
                        break;
                    default:
                        reader.Skip();
                        break;
                }
            }
        }

        return requestSettings;
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, T value, JsonSerializerOptions options)
    {
        writer.WriteStartObject();

        writer.WriteNumber("temperature", value.Temperature);
        writer.WriteNumber("top_p", value.TopP);
        writer.WriteNumber("frequency_penalty", value.FrequencyPenalty);
        writer.WriteNumber("presence_penalty", value.PresencePenalty);
        if (value.MaxTokens is null)
        {
            writer.WriteNull("max_tokens");
        }
        else
        {
            writer.WriteNumber("max_tokens", (decimal)value.MaxTokens);
        }
        writer.WritePropertyName("stop_sequences");
        JsonSerializer.Serialize(writer, value.StopSequences, options);
        writer.WriteNumber("results_per_prompt", value.ResultsPerPrompt);
        writer.WriteString("chat_system_prompt", value.ChatSystemPrompt);
        writer.WritePropertyName("token_selection_biases");
        JsonSerializer.Serialize(writer, value.TokenSelectionBiases, options);
        writer.WriteString("service_id", value.ServiceId);

        writer.WriteEndObject();
    }
}
