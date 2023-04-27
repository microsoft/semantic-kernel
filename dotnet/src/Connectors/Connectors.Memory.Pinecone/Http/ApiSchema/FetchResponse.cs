using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// FetchResponse
/// See https://docs.pinecone.io/reference/fetch
/// </summary>
internal class FetchResponse
{

    /// <summary>
    /// Initializes a new instance of the <see cref="FetchResponse" /> class.
    /// </summary>
    /// <param name="vectors">vectors.</param>
    /// <param name="nameSpace">An index namespace name.</param>
    [JsonConstructor]
    public FetchResponse(Dictionary<string, PineconeDocument> vectors, string? nameSpace = default)
    {
        this.Vectors = vectors;
        this.Namespace = nameSpace;
    }

    /// <summary>
    /// Gets or Sets Vectors
    /// </summary>
    [JsonPropertyName("vectors")]
    public Dictionary<string, PineconeDocument> Vectors { get; set; }

    public IEnumerable<PineconeDocument> WithoutEmbeddings()
    {
        return this.Vectors.Values.Select(v => PineconeDocument.Create(v.Id).WithMetadata(v.Metadata));
    }

    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

}
