#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.Gemini;

/// <summary>
/// Union field data can be only one of properties in class GeminiPart
/// </summary>
public sealed class GeminiPart
{
    /// <summary>
    /// Gets or sets the text data.
    /// </summary>
    [JsonPropertyName("text")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Text { get; set; }

    /// <summary>
    /// Gets or sets the image or video data.
    /// </summary>
    [JsonPropertyName("inlineData")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartInlineData? InlineData { get; set; }

    /// <summary>
    /// Function call data.
    /// </summary>
    [JsonPropertyName("functionCall")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartFunctionCall? FunctionCall { get; set; }

    /// <summary>
    /// Object representing the function call response.
    /// </summary>
    [JsonPropertyName("functionResponse")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiPartFunctionResponse? FunctionResponse { get; set; }

    /// <summary>
    /// Checks whether only one property of the GeminiPart instance is not null.
    /// Returns true if only one property among Text, InlineData, FunctionCall, and FunctionResponse is not null,
    /// Otherwise, it returns false.
    /// </summary>
    public bool IsValid()
    {
        return (this.Text != null ? 1 : 0) +
            (this.InlineData != null ? 1 : 0) +
            (this.FunctionCall != null ? 1 : 0) +
            (this.FunctionResponse != null ? 1 : 0) == 1;
    }
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
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<JsonNode>? Arguments { get; set; }
}

public sealed class GeminiPartFunctionResponse
{
    [JsonPropertyName("name")]
    public string FunctionName { get; set; }

    [JsonPropertyName("response")]
    public IList<JsonNode> Response { get; set; }
}
