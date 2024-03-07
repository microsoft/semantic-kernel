// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

internal sealed class VertexAIHttpRequestFactory : IHttpRequestFactory
{
    private readonly string _bearerKey;

    public VertexAIHttpRequestFactory(string bearerKey)
    {
        Verify.NotNullOrWhiteSpace(bearerKey);

        this._bearerKey = bearerKey;
    }

    public HttpRequestMessage CreatePost(object requestData, Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(VertexAIHttpRequestFactory)));
        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._bearerKey}");
        return httpRequestMessage;
    }
}
