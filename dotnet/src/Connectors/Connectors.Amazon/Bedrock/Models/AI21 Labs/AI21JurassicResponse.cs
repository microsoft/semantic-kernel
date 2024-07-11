// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.AI21;

[Serializable]
public class AI21JurassicResponse
{
    [JsonPropertyName("id")]
    public long Id { get; set; }

    [JsonPropertyName("prompt")]
    public PromptText Prompt { get; set; }

    [JsonPropertyName("completions")]
    public List<Completion> Completions { get; set; }
}

[Serializable]
public class PromptText
{
    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("tokens")]
    public List<Token> Tokens { get; set; }
}

[Serializable]
public class Token
{
    [JsonPropertyName("generatedToken")]
    public GeneratedToken GeneratedToken { get; set; }

    [JsonPropertyName("topTokens")]
    public object TopTokens { get; set; }

    [JsonPropertyName("textRange")]
    public TextRange TextRange { get; set; }
}

[Serializable]
public class GeneratedToken
{
    [JsonPropertyName("token")]
    public string TokenValue { get; set; }

    [JsonPropertyName("logprob")]
    public double Logprob { get; set; }

    [JsonPropertyName("raw_logprob")]
    public double RawLogprob { get; set; }
}

[Serializable]
public class TextRange
{
    [JsonPropertyName("start")]
    public int Start { get; set; }

    [JsonPropertyName("end")]
    public int End { get; set; }
}

[Serializable]
public class Completion
{
    [JsonPropertyName("data")]
    public Data Data { get; set; }

    [JsonPropertyName("finishReason")]
    public FinishReason FinishReason { get; set; }
}

[Serializable]
public class Data
{
    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("tokens")]
    public List<Token> Tokens { get; set; }
}

[Serializable]
public class FinishReason
{
    [JsonPropertyName("reason")]
    public string Reason { get; set; }

    [JsonPropertyName("length")]
    public int Length { get; set; }
}
