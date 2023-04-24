using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Vector sparse data. Represented as a list of indices and a list of corresponded values, which must be the same length.
/// </summary>
public class SparseVectorData
{

    /// <summary>
    /// The indices of the sparse data.
    /// </summary>
    /// <value>The indices of the sparse data.</value>
    [JsonPropertyName("indices")]
    [JsonRequired]
    public IEnumerable<long> Indices { get; set; }

    /// <summary>
    /// The corresponding values of the sparse data, which must be the same length as the indices.
    /// </summary>
    /// <value>The corresponding values of the sparse data, which must be the same length as the indices.</value>
    [JsonPropertyName("values")]
    [JsonRequired]
    public IEnumerable<float> Values { get; set; }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("class SparseVectorData {\n");
        sb.Append("  Indices: ").Append(this.Indices).Append('\n');
        sb.Append("  Values: ").Append(this.Values).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    public static SparseVectorData CreateSparseVectorData(List<long> indices, List<float> values)
    {
        return new SparseVectorData(indices, values);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SparseVectorData" /> class.
    /// </summary>
    /// <param name="indices">The indices of the sparse data. (required).</param>
    /// <param name="values">The corresponding values of the sparse data, which must be the same length as the indices. (required).</param>
    [JsonConstructor]
    public SparseVectorData(List<long> indices, List<float> values)
    {
        this.Indices = indices;
        this.Values = values;
    }

}
