using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// FetchResponse
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
    /// <value>An index namespace name</value>
    /// <example>&quot;namespace-0&quot;</example>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("FetchResponse {\n");
        sb.Append("  Vectors: ").Append(this.Vectors).Append('\n');
        sb.Append("  Namespace: ").Append(this.Namespace).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

}
