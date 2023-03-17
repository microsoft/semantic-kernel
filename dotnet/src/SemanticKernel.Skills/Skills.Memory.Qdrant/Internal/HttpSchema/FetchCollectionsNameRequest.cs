// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.HttpSchema;

internal class FetchCollectionNameRequest
{
    public static FetchCollectionNameRequest Fetch()
    {
        return new FetchCollectionNameRequest();
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
