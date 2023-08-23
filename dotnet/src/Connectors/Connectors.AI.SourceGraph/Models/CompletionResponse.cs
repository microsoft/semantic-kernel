// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;

#pragma warning disable CS8618, CS8601, CS8603
internal class CompletionResponse
{
    [JsonPropertyName("completion")]
    public string? Completion { get; set; }

    [JsonPropertyName("stopReason")]
    public string? StopReason { get; set; }
}
