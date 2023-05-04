// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// DeleteRequest
/// See https://docs.pinecone.io/reference/delete_post
/// </summary>
internal sealed class DeleteRequest
{
    /// <summary>
    /// The ids of the vectors to delete
    /// </summary>
    [JsonPropertyName("ids")]
    public IEnumerable<string>? Ids { get; set; }

    /// <summary>
    /// Whether to delete all vectors
    /// </summary>
    [JsonPropertyName("deleteAll")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? DeleteAll { get; set; }

    /// <summary>
    /// The namespace to delete vectors from
    /// </summary>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    [JsonPropertyName("filter")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Dictionary<string, object>? Filter { get; set; }

    public static DeleteRequest GetDeleteAllVectorsRequest()
    {
        return new DeleteRequest(true);
    }

    public static DeleteRequest ClearNamespace(string indexNamespace)
    {
        return new DeleteRequest(true)
        {
            Namespace = indexNamespace
        };
    }

    public static DeleteRequest DeleteVectors(IEnumerable<string>? ids)
    {
        return new DeleteRequest(ids);
    }

    public DeleteRequest FilterBy(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    public DeleteRequest FromNamespace(string? indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    public DeleteRequest Clear(bool deleteAll)
    {
        this.DeleteAll = deleteAll;
        return this;
    }

    public HttpRequestMessage Build()
    {
        if (this.Filter != null)
        {
            this.Filter = PineconeUtils.ConvertFilterToPineconeFilter(this.Filter);
        }

        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/vectors/delete",
            this);

        request.Headers.Add("accept", "application/json");

        return request;
    }

    /// <inheritdoc />
    public override string ToString()
    {
        var sb = new StringBuilder();

        sb.Append("DeleteRequest: ");

        if (this.Ids != null)
        {
            sb.Append($"Deleting {this.Ids.Count()} vectors, {string.Join(", ", this.Ids)},");
        }

        if (this.DeleteAll != null)
        {
            sb.Append("Deleting All vectors,");
        }

        if (this.Namespace != null)
        {
            sb.Append($"From Namespace: {this.Namespace}, ");
        }

        if (this.Filter == null)
        {
            return sb.ToString();
        }

        sb.Append("With Filter: ");

        foreach (var pair in this.Filter)
        {
            sb.Append($"{pair.Key}={pair.Value}, ");
        }

        return sb.ToString();
    }

    #region private ================================================================================

    private DeleteRequest(IEnumerable<string>? ids)
    {
        this.Ids = ids ?? new List<string>();
    }

    private DeleteRequest(bool clear)
    {
        this.Ids = new List<string>();
        this.DeleteAll = clear;
    }

    #endregion
}
