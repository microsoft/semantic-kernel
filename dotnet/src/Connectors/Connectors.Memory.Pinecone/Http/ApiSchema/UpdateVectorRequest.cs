using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// UpdateRequest
/// </summary>
internal class UpdateVectorRequest
{

    /// <summary>
    /// The vectors unique ID
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    [JsonPropertyName("values")]
    public IEnumerable<float>? Values { get; set; }

    /// <summary>
    ///  The sparse vector data
    /// </summary>
    [JsonPropertyName("sparseValues")]
    public SparseVectorData? SparseValues { get; set; }

    /// <summary>
    /// The metadata to set
    /// </summary>
    [JsonPropertyName("setMetadata")]
    public Dictionary<string, object>? Metadata { get; set; }

    /// <summary>
    /// The namespace the vector belongs to
    /// </summary>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

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
