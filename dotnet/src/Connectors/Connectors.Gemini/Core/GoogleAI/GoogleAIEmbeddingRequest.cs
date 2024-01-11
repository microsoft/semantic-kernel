#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.GoogleAI;

internal sealed class GoogleAIEmbeddingRequest
{
    [JsonPropertyName("requests")]
    public IList<GoogleAIGeminiEmbeddingRequestEmbedContent> Requests { get; set; }

    public static GoogleAIEmbeddingRequest FromData(IEnumerable<string> data, string modelId) => new()
    {
        Requests = data.Select(text => new GoogleAIGeminiEmbeddingRequestEmbedContent
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

internal sealed class GoogleAIGeminiEmbeddingRequestEmbedContent
{
    [JsonPropertyName("model")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Model { get; set; }

    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    [JsonPropertyName("content")]
    public GeminiRequestContent Content { get; set; }

    [JsonPropertyName("taskType")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TaskType { get; set; } // todo: enum
}
