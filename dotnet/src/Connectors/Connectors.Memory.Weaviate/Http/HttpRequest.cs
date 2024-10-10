// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal static class HttpRequest
{
    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public static HttpRequestMessage CreateGetRequest(string url, object? payload = null)
    {
        return new(HttpMethod.Get, url)
        {
            Content = GetJsonContent(payload)
        };
    }

    public static HttpRequestMessage CreatePostRequest(string url, object? payload = null)
    {
        return new(HttpMethod.Post, url)
        {
            Content = GetJsonContent(payload)
        };
    }

    public static HttpRequestMessage CreateDeleteRequest(string url, object? payload = null)
    {
        return new(HttpMethod.Delete, url)
        {
            Content = GetJsonContent(payload)
        };
    }

    public static HttpRequestMessage CreatePutRequest(string url, object? payload = null)
    {
        return new(HttpMethod.Put, url)
        {
            Content = GetJsonContent(payload)
        };
    }

    private static StringContent? GetJsonContent(object? payload)
    {
        if (payload is null)
        {
            return null;
        }

        string strPayload = payload as string ?? JsonSerializer.Serialize(payload, s_jsonOptionsCache);
        return new(strPayload, Encoding.UTF8, "application/json");
    }
}
