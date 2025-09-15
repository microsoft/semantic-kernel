// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class GoogleAIEmbeddingRequest
{
    [JsonPropertyName("requests")]
    public IList<RequestEmbeddingContent> Requests { get; set; } = null!;

    public static GoogleAIEmbeddingRequest FromData(IEnumerable<string> data, string modelId, int? dimensions = null) => new()
    {
        Requests = data.Select(text => new RequestEmbeddingContent
        {
            Model = $"models/{modelId}",
            Content = new()
            {
                Parts =
                [
                    new()
                    {
                        Text = text
                    }
                ]
            },
            Dimensions = dimensions
        }).ToList()
    };

    internal sealed class RequestEmbeddingContent
    {
        [JsonPropertyName("model")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Model { get; set; }

        [JsonPropertyName("title")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Title { get; set; }

        [JsonPropertyName("content")]
        public GeminiContent Content { get; set; } = null!;

        [JsonPropertyName("taskType")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? TaskType { get; set; } // todo: enum

        [JsonPropertyName("outputDimensionality")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? Dimensions { get; set; }
    }
}
