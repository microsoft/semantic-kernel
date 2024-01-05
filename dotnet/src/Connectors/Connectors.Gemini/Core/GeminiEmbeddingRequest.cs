#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

internal sealed class GeminiEmbeddingRequest
{
    [JsonPropertyName("requests")]
    public IList<GeminiEmbeddingRequestEmbedContent> Requests { get; set; }

    public static GeminiEmbeddingRequest FromData(IEnumerable<string> data, string modelId) => new()
    {
        Requests = data.Select(text => new GeminiEmbeddingRequestEmbedContent
        {
            Model = $"models/{modelId}",
            Content = new()
            {
                Parts = new List<GeminiPart>
                {
                    new()
                    {
                        Text = text
                    }
                }
            }
        }).ToList()
    };
}

internal sealed class GeminiEmbeddingRequestEmbedContent
{
    [JsonPropertyName("model")]
    public string Model { get; set; }

    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    [JsonPropertyName("content")]
    public GeminiRequestContent Content { get; set; }

    [JsonPropertyName("taskType")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TaskType { get; set; } // todo: enum
}
