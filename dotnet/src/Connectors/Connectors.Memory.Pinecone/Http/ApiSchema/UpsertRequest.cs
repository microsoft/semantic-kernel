using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// UpsertRequest
/// See https://docs.pinecone.io/reference/upsert
/// </summary>
internal class UpsertRequest
{

    /// <summary>
    /// The vectors to upsert
    /// </summary>
    [JsonPropertyName("vectors")]
    public List<PineconeDocument> Vectors { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

    public static UpsertRequest UpsertVectors(IEnumerable<PineconeDocument> vectorRecords)
    {
        UpsertRequest request = new();

        foreach (PineconeDocument? vectorRecord in vectorRecords)
        {
            request.Vectors.Add(vectorRecord);
        }

        return request;
    }

    public UpsertRequest ToNamespace(string? nameSpace)
    {
        this.Namespace = nameSpace;
        return this;
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest("/vectors/upsert", this);
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private UpsertRequest()
    {
        this.Vectors = new List<PineconeDocument>();
    }

    #endregion

}
