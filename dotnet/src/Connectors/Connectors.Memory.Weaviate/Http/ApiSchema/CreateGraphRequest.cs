// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// ReSharper disable once ClassCannotBeInstantiated
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class CreateGraphRequest
{
#pragma warning disable CS8618
    public string Class { get; set; }
    public ReadOnlyMemory<float> Vector { get; set; }
#pragma warning restore CS8618
    public int Limit { get; set; }
    public bool WithVector { get; set; }
    public double Distance { get; set; }

    public HttpRequestMessage Build()
    {
        var vectors = this.Vector.ToArray();
        var vectorAsString = string.Join(",", vectors.Select(x => string.Format(CultureInfo.InvariantCulture, "{0:f}", x)));
        string payload = $"{{Get{{{this.Class}(" +
                         $"nearVector:{{vector:[{vectorAsString}] " +
                         $"distance:{this.Distance}}} " +
                         $"limit:{this.Limit}){{{(this.WithVector ? "_additional{vector}" : string.Empty)} " +
                         "_additional{id distance} sk_timestamp sk_id sk_description sk_text sk_additional_metadata}}}";
        string queryJson = $$"""{"query":"{{payload}}"}""";
        return HttpRequest.CreatePostRequest(
            "graphql",
            queryJson);
    }
}
