// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Json
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal static class HttpRequest

{
    public static HttpRequestMessage CreateGetRequest(string url)
    {
        return new HttpRequestMessage(HttpMethod.Get, url);
    }

    public static HttpRequestMessage CreatePostRequest(string url, object? payload = null)
    {
        return new HttpRequestMessage(HttpMethod.Post, url);
        /*{
            Content = GetJsonContent(payload)
        };*/
    }

    public static HttpRequestMessage CreatePutRequest(string url, object? payload = null)
    {
        return new HttpRequestMessage(HttpMethod.Put, url)''
        //{
        //    Content = GetJsonContent(payload)
        //};
    }

    public static HttpRequestMessage CreatePatchRequest(string url, object? payload = null)
    {
        return new HttpRequestMessage(HttpMethod.Patch, url)
        {
            Content = GetJsonContent(payload)
        };
    }

    public static HttpRequestMessage CreateDeleteRequest(string url)
    {
        return new HttpRequestMessage(HttpMethod.Delete, url);
    }

public static async Task SendHttpFromJsonAsync<TObject>(HttpClient httpClient, HttpMethod methodType )
{ 
    //TODO: Clean this up-TEW
    object? httpresult = null; 
    
    switch (methodType.ToString())
    {
        case "GET":
            var result = await httpClient.GetFromJsonAsync<TObject>(
                "todos?userId=1&completed=false");
            break;
        case "POST":
        {using HttpResponseMessage response = await httpClient.PostAsJsonAsync<TObject>(
                "todos?userId=1&completed=false");
                response.EnsureSuccessStatusCode();
                result = await response.Content.ReadAsStringAsync();
        }
            httpresult = result;
            break;
        case "PUT":
            var result = await httpClient.PutAsJsonAsync<TObject>(
                "todos?userId=1&completed=false");
            break;
        case "PATCH":
            var result = await httpClient.PatchAsync(
                "todos?userId=1&completed=false");
            break;
        case "DELETE":
            var result = await httpClient.DeleteAsync(
                "todos?userId=1&completed=false");
            break;
        default:
            break;
    }
    
    return httpresult; 
}
    public static StringContent? GetJsonContent(object? payload)
    {
        if (payload != null)
        {
            if (payload is string strPayload)
            {
                return new StringContent(strPayload);
            }

            var json = JsonSerializer.Serialize(payload);
            return new StringContent(json, Encoding.UTF8, MediaTypeNames.Application.Json);
        }

        return null;
    } 
}
