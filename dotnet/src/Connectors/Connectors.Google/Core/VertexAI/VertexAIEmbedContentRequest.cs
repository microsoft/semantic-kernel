// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal sealed class VertexAIEmbedContentRequest
{
    [JsonPropertyName("requests")]
    public IList<EmbedContentRequestItem> Requests { get; set; } = null!;

    public static VertexAIEmbedContentRequest FromData(IEnumerable<string> data, string model, int? dimensions = null) => new()
    {
        Requests = data.Select(text => new EmbedContentRequestItem
        {
            Model = model,
            Content = new RequestContent
            {
                Parts =
                [
                    new RequestPart
                    {
                        Text = text
                    }
                ]
            },
            OutputDimensionality = dimensions
        }).ToList()
    };

    internal sealed class EmbedContentRequestItem
    {
        [JsonPropertyName("model")]
        public string Model { get; set; } = null!;

        [JsonPropertyName("content")]
        public RequestContent Content { get; set; } = null!;

        [JsonPropertyName("outputDimensionality")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? OutputDimensionality { get; set; }
    }

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
