// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbeddingRequest
{
    [JsonPropertyName("instances")]
    public IList<RequestContent> Requests { get; set; } = null!;

    [JsonPropertyName("parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public RequestParameters? Parameters { get; set; }

    public static VertexAIEmbeddingRequest FromData(IEnumerable<string> data) => new()
    {
        Requests = data.Select(text => new RequestContent
        {
            Content = text
        }).ToList(),
        Parameters = new RequestParameters
        {
            // todo make configurable when ITextEmbeddingGenerationService will support parameters
            AutoTruncate = false
        }
    };

    internal sealed class RequestContent
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

    internal sealed class RequestParameters
    {
        [JsonPropertyName("autoTruncate")]
        public bool AutoTruncate { get; set; }
    }
}
