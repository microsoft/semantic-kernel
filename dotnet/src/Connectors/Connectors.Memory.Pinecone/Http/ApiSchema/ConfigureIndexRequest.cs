// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// This operation specifies the pod type and number of replicas for an index.
/// See https://docs.pinecone.io/reference/configure_index
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class ConfigureIndexRequest
{
    public string IndexName { get; set; }

    /// <summary>
    /// Gets or Sets PodType
    /// </summary>
    [JsonPropertyName("pod_type")]
    public PodType PodType { get; set; }

    /// <summary>
    /// The desired number of replicas for the index.
    /// </summary>
    /// <value>The desired number of replicas for the index.</value>
    [JsonPropertyName("replicas")]
    public int Replicas { get; set; }

    public static ConfigureIndexRequest Create(string indexName)
    {
        return new ConfigureIndexRequest(indexName);
    }

    public ConfigureIndexRequest WithPodType(PodType podType)
    {
        this.PodType = podType;
        return this;
    }

    public ConfigureIndexRequest NumberOfReplicas(int replicas)
    {
        this.Replicas = replicas;
        return this;
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreatePatchRequest(
            $"/databases/{this.IndexName}", this);

        request.Headers.Add("accept", "text/plain");

        return request;
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="ConfigureIndexRequest" /> class.
    /// </summary>
    /// <param name="indexName"> Name of the index.</param>
    private ConfigureIndexRequest(string indexName)
    {
        this.IndexName = indexName;
    }

    #endregion
}
