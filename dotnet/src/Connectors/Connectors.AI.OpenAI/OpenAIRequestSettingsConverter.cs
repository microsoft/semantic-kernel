// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// JSON converter for <see cref="OpenAIRequestSettings"/>
/// </summary>
public class OpenAIRequestSettingsConverter : JsonConverter<OpenAIRequestSettings>
{
    /// <inheritdoc/>
    public override OpenAIRequestSettings? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var requestSettings = new OpenAIRequestSettings();

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType == JsonTokenType.PropertyName)
            {
                string? propertyName = reader.GetString();

                if (propertyName is not null)
                {
                    // normalise property name to uppercase without "_" to support pascalcase, snakecase, etc.
                    propertyName = propertyName.ToUpperInvariant().Replace("_", string.Empty);
                }

                reader.Read();

                switch (propertyName)
                {
                    case "TEMPERATURE":
                        requestSettings.Temperature = reader.GetDouble();
                        break;
                    case "TOPP":
                        requestSettings.TopP = reader.GetDouble();
                        break;
                    case "FREQUENCYPENALTY":
                        requestSettings.FrequencyPenalty = reader.GetDouble();
                        break;
                    case "PRESENCEPENALTY":
                        requestSettings.PresencePenalty = reader.GetDouble();
                        break;
                    case "MAXTOKENS":
                        requestSettings.MaxTokens = reader.GetInt32();
                        break;
                    case "STOPSEQUENCES":
                        requestSettings.StopSequences = JsonSerializer.Deserialize<IList<string>>(ref reader, options) ?? Array.Empty<string>();
                        break;
                    case "RESULTSPERPROMPT":
                        requestSettings.ResultsPerPrompt = reader.GetInt32();
                        break;
                    case "CHATSYSTEMPROMPT":
                        requestSettings.ChatSystemPrompt = reader.GetString() ?? OpenAIRequestSettings.DefaultChatSystemPrompt;
                        break;
                    case "TOKENSELECTIONBIASES":
                        requestSettings.TokenSelectionBiases = JsonSerializer.Deserialize<IDictionary<int, int>>(ref reader, options) ?? new Dictionary<int, int>();
                        break;
                    case "SERVICEID":
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
    public override void Write(Utf8JsonWriter writer, OpenAIRequestSettings value, JsonSerializerOptions options)
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
