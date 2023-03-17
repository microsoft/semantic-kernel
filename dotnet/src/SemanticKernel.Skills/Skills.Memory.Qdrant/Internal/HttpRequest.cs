// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net.Http.Json;
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
        return new HttpRequestMessage(HttpMethod.Put, url);
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

public static async Task<TResult> SendHttpFromJsonAsync<TObject, TResult>(HttpClient httpClient, HttpMethod methodType, string qdranturl, TObject httpContentData)
{ 
    //TODO: Clean this up-TEW

    HttpResponseMessage httpResponse;
    TResult httpresult = default!;  
    
    switch (methodType.ToString())
    {
        case string mType when HttpMethod.Get.ToString() == methodType.ToString():
            var getResult = await httpClient.GetFromJsonAsync<TObject>(qdranturl);
            break;
        case string mType when HttpMethod.Post.ToString() == methodType.ToString():
            /*{using HttpResponseMessage response = await httpClient.PostAsJsonAsync<TObject>(
                    qdranturl);
                    response.EnsureSuccessStatusCode();
                    httpResponse = response;
            }*/
            break;
        case string mType when HttpMethod.Put.ToString() == methodType.ToString():
            { 
                using HttpResponseMessage response = await httpClient.PutAsJsonAsync(
                qdranturl,
                httpContentData);

                httpResponse = response;
            }
            //var putResult = await httpClient.PutAsJsonAsync<TObject>(qdranturl);
            break;
        case string mType when HttpMethod.Patch.ToString() == methodType.ToString():
            //var pathResult = await httpClient.PatchAsync(qdranturl);
            break;
        case string mType when HttpMethod.Delete.ToString() == methodType.ToString():
           // var deleteResult = await httpClient.DeleteAsync(qdranturl);
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
