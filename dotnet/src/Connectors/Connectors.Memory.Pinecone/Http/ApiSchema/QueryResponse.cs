using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// QueryResponse
/// See https://docs.pinecone.io/reference/query
/// </summary>
internal class QueryResponse
{

    /// <summary>
    /// Initializes a new instance of the <see cref="QueryResponse" /> class.
    /// </summary>
    /// <param name="matches">matches.</param>
    /// <param name="nameSpace">An index namespace name.</param>
    public QueryResponse(List<PineconeDocument> matches, string? nameSpace = default)
    {
        this.Matches = matches;
        this.Namespace = nameSpace;
    }

    /// <summary>
    /// Gets or Sets Matches
    /// </summary>
    [JsonPropertyName("matches")]
    public List<PineconeDocument> Matches { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    /// <value>An index namespace name</value>
    /// <example>&quot;namespace-0&quot;</example>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

}
