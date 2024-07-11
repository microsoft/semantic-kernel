// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.AI21;

public class AI21JurassicRequest
{
    [Serializable]
public class AI21JurassicTextGenerationRequest : ITextGenerationRequest
{
    [JsonIgnore]
    public string InputText
    {
        get
        {
            return Prompt;
        }
    }
    [JsonPropertyName("prompt")]
    public required string Prompt { get; set; }

    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature { get; set; }

    [JsonPropertyName("topP")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP { get; set; }

    [JsonPropertyName("maxTokens")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxTokens { get; set; }

    [JsonPropertyName("stopSequences")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<string>? StopSequences { get; set; }

    [JsonPropertyName("countPenalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public CountPenalty? CountPenalty { get; set; }

    [JsonPropertyName("presencePenalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public PresencePenalty? PresencePenalty { get; set; }

    [JsonPropertyName("frequencyPenalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public FrequencyPenalty? FrequencyPenalty { get; set; }

    double? ITextGenerationRequest.Temperature => Temperature;
    double? ITextGenerationRequest.TopP => TopP;
    int? ITextGenerationRequest.MaxTokens => MaxTokens;
    IList<string>? ITextGenerationRequest.StopSequences => StopSequences;
}

[Serializable]
public class CountPenalty
{
    [JsonPropertyName("scale")]
    public double Scale { get; set; }

    [JsonPropertyName("applyToWhitespaces")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToWhitespaces { get; set; }

    [JsonPropertyName("applyToPunctuations")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToPunctuations { get; set; }

    [JsonPropertyName("applyToNumbers")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToNumbers { get; set; }

    [JsonPropertyName("applyToStopwords")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToStopwords { get; set; }

    [JsonPropertyName("applyToEmojis")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToEmojis { get; set; }
}

[Serializable]
public class PresencePenalty
{
    [JsonPropertyName("scale")]
    public double Scale { get; set; }

    [JsonPropertyName("applyToWhitespaces")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToWhitespaces { get; set; }

    [JsonPropertyName("applyToPunctuations")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToPunctuations { get; set; }

    [JsonPropertyName("applyToNumbers")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToNumbers { get; set; }

    [JsonPropertyName("applyToStopwords")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToStopwords { get; set; }

    [JsonPropertyName("applyToEmojis")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToEmojis { get; set; }
}

[Serializable]
public class FrequencyPenalty
{
    [JsonPropertyName("scale")]
    public double Scale { get; set; }

    [JsonPropertyName("applyToWhitespaces")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToWhitespaces { get; set; }

    [JsonPropertyName("applyToPunctuations")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToPunctuations { get; set; }

    [JsonPropertyName("applyToNumbers")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToNumbers { get; set; }

    [JsonPropertyName("applyToStopwords")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToStopwords { get; set; }

    [JsonPropertyName("applyToEmojis")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ApplyToEmojis { get; set; }
}
}
