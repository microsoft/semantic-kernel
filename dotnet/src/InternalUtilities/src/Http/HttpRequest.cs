// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Microsoft.SemanticKernel;

internal static class HttpRequest
{
    private static readonly HttpMethod s_patchMethod = new("PATCH");

    public static HttpRequestMessage CreateGetRequest(string url, object? payload = null) =>
        CreateRequest(HttpMethod.Get, url, payload);

    public static HttpRequestMessage CreatePostRequest(string url, object? payload = null) =>
        CreateRequest(HttpMethod.Post, url, payload);

    public static HttpRequestMessage CreatePostRequest(Uri url, object? payload = null) =>
        CreateRequest(HttpMethod.Post, url, payload);

    public static HttpRequestMessage CreatePutRequest(string url, object? payload = null) =>
        CreateRequest(HttpMethod.Put, url, payload);

    public static HttpRequestMessage CreatePatchRequest(string url, object? payload = null) =>
        CreateRequest(s_patchMethod, url, payload);

    public static HttpRequestMessage CreateDeleteRequest(string url, object? payload = null) =>
        CreateRequest(HttpMethod.Delete, url, payload);

    private static HttpRequestMessage CreateRequest(HttpMethod method, string url, object? payload) =>
        new(method, url) { Content = CreateJsonContent(payload) };

    private static HttpRequestMessage CreateRequest(HttpMethod method, Uri url, object? payload) =>
        new(method, url) { Content = CreateJsonContent(payload) };

    private static HttpContent? CreateJsonContent(object? payload)
    {
        HttpContent? content = null;
        if (payload is not null)
        {
            byte[] utf8Bytes = payload is string s ?
                Encoding.UTF8.GetBytes(s) :
                JsonSerializer.SerializeToUtf8Bytes(payload);

            content = new ByteArrayContent(utf8Bytes);
            content.Headers.ContentType = new MediaTypeHeaderValue("application/json") { CharSet = "utf-8" };
        }

        return content;
    }
}
