// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests;

public sealed class FakeHttpRequestFactory : IHttpRequestFactory
{
    public HttpRequestMessage CreatePost(object requestData, Uri endpoint)
        => new(HttpMethod.Post, endpoint)
        {
            Content = new StringContent(JsonSerializer.Serialize(requestData))
        };
}
