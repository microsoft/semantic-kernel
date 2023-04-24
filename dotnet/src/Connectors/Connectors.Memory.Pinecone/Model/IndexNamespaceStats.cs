using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// IndexNamespaceStats
/// </summary>
public class IndexNamespaceStats
{

    /// <summary>
    /// Initializes a new instance of the <see cref="IndexNamespaceStats" /> class.
    /// </summary>
    /// <param name="vectorCount">vectorCount.</param>
    public IndexNamespaceStats(long vectorCount = default)
    {
        this.VectorCount = vectorCount;
    }

    /// <summary>
    /// Gets or Sets VectorCount
    /// </summary>
    [JsonPropertyName("vectorCount")]
    public long VectorCount { get; }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        return "VectorCount: " + this.VectorCount;
    }

}
