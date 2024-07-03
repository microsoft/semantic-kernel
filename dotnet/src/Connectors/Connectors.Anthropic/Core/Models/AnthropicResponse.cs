// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class AnthropicResponse
{
    [JsonRequired]
    [JsonPropertyName("id")]
    public string Id { get; init; } = null!;

    [JsonRequired]
    [JsonPropertyName("type")]
    public string Type { get; init; } = null!;

    [JsonRequired]
    [JsonPropertyName("role")]
    [JsonConverter(typeof(AuthorRoleConverter))]
    public AuthorRole Role { get; init; }

    [JsonRequired]
    [JsonPropertyName("content")]
    public IReadOnlyList<AnthropicContent> Contents { get; init; } = null!;

    [JsonRequired]
    [JsonPropertyName("model")]
    public string ModelId { get; init; } = null!;

    [JsonPropertyName("stop_reason")]
    public AnthropicFinishReason? StopReason { get; init; }

    [JsonPropertyName("stop_sequence")]
    public string? StopSequence { get; init; }

    [JsonRequired]
    [JsonPropertyName("usage")]
    public AnthropicUsage Usage { get; init; } = null!;
}
