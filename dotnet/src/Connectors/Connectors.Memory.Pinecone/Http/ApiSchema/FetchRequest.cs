// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// FetchRequest
/// See https://docs.pinecone.io/reference/fetch
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class FetchRequest
{
    /// <summary>
    /// Gets or Sets Ids
    /// </summary>
    [JsonPropertyName("ids")]
    public List<string> Ids { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    public static FetchRequest FetchVectors(IEnumerable<string> ids)
    {
        return new FetchRequest(ids);
    }

    public FetchRequest FromNamespace(string indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    public HttpRequestMessage Build()
    {
        string path = "/vectors/fetch?";
        string ids = string.Join("&", this.Ids.Select(id => "ids=" + id));

        path += ids;

        if (!string.IsNullOrEmpty(this.Namespace))
        {
            path += $"&namespace={this.Namespace}";
        }

        HttpRequestMessage request = HttpRequest.CreateGetRequest(path);

        request.Headers.Add("accept", "application/json");

        return request;
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="FetchRequest" /> class.
    /// </summary>
    private FetchRequest(IEnumerable<string> ids)
    {
        this.Ids = ids.ToList();
    }

    #endregion
}
