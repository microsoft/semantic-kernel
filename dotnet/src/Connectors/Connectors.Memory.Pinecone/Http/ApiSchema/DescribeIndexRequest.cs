using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// Get information about an index.
/// See https://docs.pinecone.io/reference/describe_index
/// </summary>
internal class DescribeIndexRequest
{
    /// <summary>
    /// The unique name of an index.
    /// </summary>
    public string IndexName { get; }

    public static DescribeIndexRequest Create(string indexName)
    {
        return new DescribeIndexRequest(indexName);
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreateGetRequest(
            $"/databases/{this.IndexName}");

        return request;
    }

    #region private ================================================================================

    private DescribeIndexRequest(string indexName)
    {
        this.IndexName = indexName;
    }

    #endregion

}
