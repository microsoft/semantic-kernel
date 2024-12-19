// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class NovaMessage
{
    internal sealed class Content
    {
        public string? Text { get; set; }
    }

    [JsonPropertyName("content")]
    public List<Content>? Contents { get; set; }

    public string? Role { get; set; }
}

internal sealed class Output
{
    public NovaMessage? Message { get; set; }
}

internal sealed class Usage
{
    public int InputTokens { get; set; }

    public int OutputTokens { get; set; }

    public int TotalTokens { get; set; }
}

/// <summary>
/// The Amazon Titan Text response object when deserialized from Invoke Model call.
/// </summary>
internal sealed class NovaTextResponse
{
    public Output? Output { get; set; }

    public Usage? Usage { get; set; }

    public string? StopReason { get; set; }
}
