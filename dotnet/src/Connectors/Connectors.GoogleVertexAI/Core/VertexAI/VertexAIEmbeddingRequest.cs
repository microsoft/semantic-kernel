#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.VertexAI;

internal sealed class VertexAIEmbeddingRequest
{
    [JsonPropertyName("instances")]
    public IList<VertexAIGeminiEmbeddingRequestEmbedContent> Requests { get; set; } = null!;

    [JsonPropertyName("parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public VertexAIEmbeddingParameters? Parameters { get; set; }

    public static VertexAIEmbeddingRequest FromData(IEnumerable<string> data) => new()
    {
        Requests = data.Select(text => new VertexAIGeminiEmbeddingRequestEmbedContent
        {
            Content = text
        }).ToList(),
        Parameters = new VertexAIEmbeddingParameters
        {
            // todo make configurable when ITextEmbeddingGenerationService will support parameters
            AutoTruncate = false
        }
    };
}

internal sealed class VertexAIGeminiEmbeddingRequestEmbedContent
{
    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; } = null!;

    [JsonPropertyName("taskType")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TaskType { get; set; } // todo: enum
}

internal sealed class VertexAIEmbeddingParameters
{
    [JsonPropertyName("autoTruncate")]
    public bool AutoTruncate { get; set; }
}
