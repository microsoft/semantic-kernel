// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.Cohere;

public class CommandRTextResponse
{
    [JsonPropertyName("response_id")]
    public string ResponseId { get; set; }

    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("generation_id")]
    public string GenerationId { get; set; }

    [JsonPropertyName("citations")]
    public List<Citation> Citations { get; set; }

    [JsonPropertyName("prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string Prompt { get; set; }

    [JsonPropertyName("finish_reason")]
    public string FinishReason { get; set; }

    [JsonPropertyName("tool_calls")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<ToolCall> ToolCalls { get; set; }

    [JsonPropertyName("meta")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Meta Meta { get; set; }
}

[Serializable]
public class Citation
{
    [JsonPropertyName("start")]
    public int Start { get; set; }

    [JsonPropertyName("end")]
    public int End { get; set; }

    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("document_ids")]
    public List<string> DocumentIds { get; set; }
}

[Serializable]
public class ToolCall
{
    [JsonPropertyName("name")]
    public string Name { get; set; }

    [JsonPropertyName("parameters")]
    public Dictionary<string, string> Parameters { get; set; }
}

[Serializable]
public class Meta
{
    [JsonPropertyName("api_version")]
    public ApiVersion ApiVersion { get; set; }

    [JsonPropertyName("billed_units")]
    public BilledUnits BilledUnits { get; set; }
}

[Serializable]
public class ApiVersion
{
    [JsonPropertyName("version")]
    public string Version { get; set; }
}

[Serializable]
public class BilledUnits
{
    [JsonPropertyName("input_tokens")]
    public int InputTokens { get; set; }

    [JsonPropertyName("output_tokens")]
    public int OutputTokens { get; set; }
}
