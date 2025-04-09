// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Represents a chat completion chunk from Mistral.
/// </summary>
internal sealed class MistralChatCompletionChunk
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("object")]
    public string? Object { get; set; }

    [JsonPropertyName("created")]
    public int Created { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }

    [JsonPropertyName("choices")]
    public List<MistralChatCompletionChoice>? Choices { get; set; }

    [JsonPropertyName("usage")]
    public MistralUsage? Usage { get; set; }

    internal IReadOnlyDictionary<string, object?>? GetMetadata() =>
        this._metadata ??= new Dictionary<string, object?>(4)
        {
            { nameof(MistralChatCompletionChunk.Id), this.Id },
            { nameof(MistralChatCompletionChunk.Model), this.Model },
            { nameof(MistralChatCompletionChunk.Created), this.Created },
            { nameof(MistralChatCompletionChunk.Object), this.Object },
            { nameof(MistralChatCompletionChunk.Usage), this.Usage },
        };

    internal int GetChoiceCount() => this.Choices?.Count ?? 0;

    internal string? GetRole(int index) => this.Choices?[index]?.Delta?.Role;

    internal string? GetContent(int index) => this.Choices?[index]?.Delta?.Content?.ToString();

    internal int GetChoiceIndex(int index) => this.Choices?[index]?.Index ?? -1;

    internal Encoding? GetEncoding() => null;

    private IReadOnlyDictionary<string, object?>? _metadata;
}
