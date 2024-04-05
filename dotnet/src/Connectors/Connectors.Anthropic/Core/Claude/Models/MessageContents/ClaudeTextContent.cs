// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core.Claude.Models.Contents;

internal sealed class ClaudeTextContent : ClaudeMessageContent
{
    [JsonConstructor]
    public ClaudeTextContent(string text)
    {
        this.Text = text;
    }

    /// <summary>
    /// Only used when type is "text". The text content.
    /// </summary>
    [JsonPropertyName("text")]
    public string Text { get; set; }
}
