// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

// ReSharper disable once ClassCannotBeInstantiated
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
        string payload = $"{{Get{{{this.Class}(" +
                         $"nearVector:{{vector:[{string.Join(",", MemoryMarshal.ToEnumerable(this.Vector))}] " +
                         $"distance:{this.Distance}}} " +
                         $"limit:{this.Limit}){{{(this.WithVector ? "_additional{vector}" : string.Empty)} " +
                         "_additional{id distance} sk_timestamp sk_id sk_description sk_text sk_additional_metadata}}}";
        string queryJson = $"{{\"query\":\"{payload}\"}}";
        return HttpRequest.CreatePostRequest(
            "graphql",
            queryJson);
    }
}
