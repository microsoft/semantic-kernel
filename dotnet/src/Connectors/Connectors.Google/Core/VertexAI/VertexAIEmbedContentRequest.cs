// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbedContentRequest
{
    [JsonPropertyName("content")]
    public RequestContent Content { get; set; } = null!;

    [JsonPropertyName("outputDimensionality")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? OutputDimensionality { get; set; }

    public static VertexAIEmbedContentRequest FromText(string text, int? dimensions = null) => new()
    {
        Content = new RequestContent
        {
            Parts = [new RequestPart { Text = text }]
        },
        OutputDimensionality = dimensions
    };

    internal sealed class RequestContent
    {
        [JsonPropertyName("parts")]
        public IList<RequestPart> Parts { get; set; } = null!;
    }

    internal sealed class RequestPart
    {
        [JsonPropertyName("text")]
        public string Text { get; set; } = null!;
    }
}
