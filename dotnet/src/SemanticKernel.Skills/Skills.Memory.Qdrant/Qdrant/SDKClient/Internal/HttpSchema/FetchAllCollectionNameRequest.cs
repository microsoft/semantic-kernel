using System.Net.Http;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.HttpSchema;

internal class FetchAllCollectionNameRequest 
{
    public static FetchAllCollectionNameRequest Fetch()
    {
        return new FetchAllCollectionNameRequest();
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest($"collections");
    }

    #region private ================================================================================
    private FetchAllCollectionNameRequest()
    {
    }

    #endregion  

}