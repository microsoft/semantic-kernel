// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class HuggingFaceHttpRequestFactory : IHttpRequestFactory
{
    public HttpRequestMessage CreatePost(object requestData, Uri endpoint, string? apiKey)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));
        if (!string.IsNullOrEmpty(apiKey))
        {
            httpRequestMessage.Headers.Add("Authorization", $"Bearer {apiKey}");
        }

        return httpRequestMessage;
    }
}
