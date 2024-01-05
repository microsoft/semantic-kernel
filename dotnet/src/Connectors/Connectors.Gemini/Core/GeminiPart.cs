#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Union field data can be only one of properties in class GeminiPart
/// </summary>
public sealed class GeminiPart
{
    [JsonPropertyName("text")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Text { get; set; }

    [JsonPropertyName("inlineData")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartInlineData? InlineData { get; set; }

    [JsonPropertyName("functionCall")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartFunctionCall? FunctionCall { get; set; }

    [JsonPropertyName("functionResponse")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartFunctionResponse? FunctionResponse { get; set; }
}

public sealed class GeminiPartInlineData
{
    [JsonPropertyName("mimeType")]
    public string MimeType { get; set; }

    /// <summary>
    /// Base64 encoded data
    /// </summary>
    [JsonPropertyName("data")]
    public string InlineData { get; set; }
}

public sealed class GeminiPartFunctionCall
{
    [JsonPropertyName("name")]
    public string FunctionName { get; set; }

    [JsonPropertyName("args")]
    public IList<JsonNode>? Arguments { get; set; }
}

public sealed class GeminiPartFunctionResponse
{
    [JsonPropertyName("name")]
    public string FunctionName { get; set; }

    [JsonPropertyName("response")]
    public IList<JsonNode> Response { get; set; }
}
