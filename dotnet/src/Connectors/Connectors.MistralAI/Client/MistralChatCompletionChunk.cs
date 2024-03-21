// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Represents a chat completion chunk from Mistral.
/// </summary>
internal class MistralChatCompletionChunk
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

    internal IReadOnlyDictionary<string, object?>? GetMetadata()
    {
        if (this._metadata is null)
        {
            this._metadata = new Dictionary<string, object?>(4)
            {
                { nameof(MistralChatCompletionChunk.Id), this.Id },
                { nameof(MistralChatCompletionChunk.Model), this.Model },
                { nameof(MistralChatCompletionChunk.Created), this.Created },
                { nameof(MistralChatCompletionChunk.Object), this.Object },
                { nameof(MistralChatCompletionChunk.Usage), this.Usage },
            };
        }

        return this._metadata;
    }

    internal int GetChoiceCount()
    {
        return this.Choices?.Count ?? 0;
    }

    internal AuthorRole? GetRole(int index)
    {
        var role = this.Choices?[index]?.Delta?.Role;
        return role is null ? null : new AuthorRole(role);
    }

    internal string? GetContent(int index)
    {
        return this.Choices?[index]?.Delta?.Content;
    }

    internal int GetChoiceIndex(int index)
    {
        return this.Choices?[index]?.Index ?? -1;
    }

    internal Encoding? GetEncoding()
    {
        return null;
    }

    private IReadOnlyDictionary<string, object?>? _metadata;
}
