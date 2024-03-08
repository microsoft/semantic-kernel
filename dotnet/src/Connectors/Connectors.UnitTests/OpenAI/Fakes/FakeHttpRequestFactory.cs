// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

public sealed class FakeHttpRequestFactory : IHttpRequestFactory
{
    public HttpRequestMessage CreatePost(object requestData, Uri endpoint)
    {
        return new HttpRequestMessage(HttpMethod.Post, endpoint)
        {
            Content = new StringContent(JsonSerializer.Serialize(requestData))
        };
    }
}
