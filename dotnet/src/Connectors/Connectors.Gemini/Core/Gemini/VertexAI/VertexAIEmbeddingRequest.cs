#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.Gemini.VertexAI;

internal sealed class VertexAIEmbeddingRequest
{
    [JsonPropertyName("instances")]
    public IList<VertexAIGeminiEmbeddingRequestEmbedContent> Requests { get; set; }

    public static VertexAIEmbeddingRequest FromData(IEnumerable<string> data, string modelId) => new()
    {
        Requests = data.Select(text => new VertexAIGeminiEmbeddingRequestEmbedContent
        {
            Content = text
        }).ToList()
    };
}

internal sealed class VertexAIGeminiEmbeddingRequestEmbedContent
{
    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; }

    [JsonPropertyName("taskType")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TaskType { get; set; } // todo: enum
}
