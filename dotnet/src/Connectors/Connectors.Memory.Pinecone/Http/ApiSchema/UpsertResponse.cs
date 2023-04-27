using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// UpsertResponse
/// See https://docs.pinecone.io/reference/upsert
/// </summary>
internal class UpsertResponse
{

    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertResponse" /> class.
    /// </summary>
    /// <param name="upsertedCount">upsertedCount.</param>
    public UpsertResponse(int upsertedCount = default)
    {
        this.UpsertedCount = upsertedCount;
    }

    /// <summary>
    /// Gets or Sets UpsertedCount
    /// </summary>
    [JsonPropertyName("upsertedCount")]
    public int UpsertedCount { get; set; }

}
