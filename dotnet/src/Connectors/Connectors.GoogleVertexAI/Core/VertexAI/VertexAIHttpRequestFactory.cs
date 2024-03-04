// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

internal sealed class VertexAIHttpRequestFactory : IHttpRequestFactory
{
    private readonly string _apiKey;

    public VertexAIHttpRequestFactory(string apiKey)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
    }

    public HttpRequestMessage CreatePost(object requestData, Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(VertexAIHttpRequestFactory)));
        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        return httpRequestMessage;
    }
}
