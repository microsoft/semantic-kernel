using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

internal class DescribeIndexRequest
{
    /// <summary>
    /// The unique name of an index.
    /// </summary>
    public string IndexName { get; }

    public static DescribeIndexRequest DescribeIndex(string indexName)
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
