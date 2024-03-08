// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <inheritdoc />
internal sealed class OpenAIHttpRequestFactory : IHttpRequestFactory
{
    private readonly string _apiKey;
    private readonly string? _organization;

    public OpenAIHttpRequestFactory(string apiKey, string? organization)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
        this._organization = organization;
    }

    /// <inheritdoc />
    public HttpRequestMessage CreatePost(object requestData, Uri endpoint)
    {
        var request = HttpRequest.CreatePostRequest(endpoint, requestData);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._apiKey);
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIHttpRequestFactory)));

        if (!string.IsNullOrWhiteSpace(this._organization))
        {
            request.Headers.Add("OpenAI-Organization", this._organization);
        }

        return request;
    }
}
