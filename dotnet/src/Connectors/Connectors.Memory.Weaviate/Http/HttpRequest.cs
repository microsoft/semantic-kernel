// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http;

internal static class HttpRequest
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
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

    public static HttpRequestMessage CreateDeleteRequest(string url)
    {
        return new(HttpMethod.Delete, url);
    }

    private static StringContent? GetJsonContent(object? payload)
    {
        if (payload == null)
        {
            return null;
        }

        string strPayload = payload as string ?? JsonSerializer.Serialize(payload, s_jsonSerializerOptions);
        return new(strPayload, Encoding.UTF8, "application/json");
    }
}
