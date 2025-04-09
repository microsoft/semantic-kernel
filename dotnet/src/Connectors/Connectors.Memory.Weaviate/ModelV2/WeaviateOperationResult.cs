// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateOperationResult
{
    private const string Success = nameof(Success);

    [JsonPropertyName("errors")]
    public WeaviateOperationResultErrors? Errors { get; set; }

    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonIgnore]
    public bool? IsSuccess => this.Status?.Equals(Success, StringComparison.OrdinalIgnoreCase);
}
