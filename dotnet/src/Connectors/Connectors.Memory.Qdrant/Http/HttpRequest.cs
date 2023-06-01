// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http;

internal static class HttpRequest
{
    public static HttpRequestMessage CreateGetRequest(string url)
    {
        return new HttpRequestMessage(HttpMethod.Get, url);
    }

    public static HttpRequestMessage CreatePostRequest<TPayload>(string url, TPayload payload, JsonTypeInfo<TPayload> typeInfo)
    {
        return new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = GetJsonContent(payload, typeInfo)
        };
    }

    public static HttpRequestMessage CreatePutRequest<TPayload>(string url, TPayload payload, JsonTypeInfo<TPayload> typeInfo)
    {
        return new HttpRequestMessage(HttpMethod.Put, url)
        {
            Content = GetJsonContent(payload, typeInfo)
        };
    }

    public static HttpRequestMessage CreateDeleteRequest(string url)
    {
        return new HttpRequestMessage(HttpMethod.Delete, url);
    }

    private static ByteArrayContent? GetJsonContent<TPayload>(TPayload payload, JsonTypeInfo<TPayload> typeInfo)
    {
        ByteArrayContent? content = null;

        if (payload is not null)
        {
            content = new ByteArrayContent(payload is string s ? Encoding.UTF8.GetBytes(s) : JsonSerializer.SerializeToUtf8Bytes(payload, typeInfo));
            content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");
        }

        return content;
    }
}
