using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// UpdateRequest
/// </summary>
internal class UpdateVectorRequest
{

    /// <summary>
    /// The vector&#39;s unique ID
    /// </summary>
    /// <value>The vector&#39;s unique ID</value>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    /// <value>Vector dense data. This should be the same length as the dimension of the index being queried.</value>
    [JsonPropertyName("values")]
    public IEnumerable<float>? Values { get; set; }

    /// <summary>
    /// Gets or Sets SparseValues
    /// </summary>
    [JsonPropertyName("sparseValues")]
    public SparseVectorData? SparseValues { get; set; }

    /// <summary>
    /// Gets or Sets SetMetadata
    /// </summary>
    [JsonPropertyName("setMetadata")]
    public Dictionary<string, object>? Metadata { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    /// <value>An index namespace name</value>
    /// <example>&quot;namespace-0&quot;</example>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("UpdateRequest {\n");
        sb.Append("  Id: ").Append(this.Id).Append('\n');
        sb.Append("  Values: ").Append(this.Values).Append('\n');
        sb.Append("  SparseValues: ").Append(this.SparseValues).Append('\n');
        sb.Append("  SetMetadata: ").Append(this.Metadata).Append('\n');
        sb.Append("  Namespace: ").Append(this.Namespace).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    public static UpdateVectorRequest UpdateVector(string id)
    {
        return new UpdateVectorRequest(id);
    }

    public static UpdateVectorRequest FromPineconeDocument(PineconeDocument document)
    {
        return new UpdateVectorRequest(document.Id, document.Values)
        {
            SparseValues = document.SparseValues,
            Metadata = document.Metadata
        };
    }

    public UpdateVectorRequest InNamespace(string? nameSpace)
    {
        this.Namespace = nameSpace;
        return this;
    }

    public UpdateVectorRequest SetMetadata(Dictionary<string, object>? setMetadata)
    {
        this.Metadata = setMetadata;
        return this;
    }

    public UpdateVectorRequest UpdateSparseValues(SparseVectorData? sparseValues)
    {
        this.SparseValues = sparseValues;
        return this;
    }

    public UpdateVectorRequest UpdateValues(IEnumerable<float>? values)
    {
        this.Values = values;
        return this;
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/vectors/update", this);

        return request;
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="UpdateVectorRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private UpdateVectorRequest(string id, IEnumerable<float>? values = default)
    {
        this.Id = id;
        this.Values = values;
    }

    #endregion

}
