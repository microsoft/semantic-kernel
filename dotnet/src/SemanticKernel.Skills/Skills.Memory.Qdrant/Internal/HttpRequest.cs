// Copyright (c) Microsoft. All rights reserved.

using System;
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

    public static async Task<TResult> SendHttpFromJsonAsync<TResult>(HttpClient httpClient, HttpMethod methodType, string qdranturl, TResult? httpContentData)
    {
        TResult httpResult = default!;
        
        switch (methodType.ToString())
        {
            case nameof(HttpMethod.Get):
                try
                {
                    var Result = await httpClient.GetFromJsonAsync<TResult>(qdranturl);
                    httpResult = Result!;
                }
                catch (Exception ex)
                {
                    throw new HttpRequestException($"Error requesting Qdrant data: {ex.Message}");
                }
                break;

            case nameof(HttpMethod.Post):
                {
                    using HttpResponseMessage httpResponse = 
                        await httpClient.PostAsJsonAsync<TResult>(qdranturl, httpContentData!);
                    try
                    {
                        httpResponse.EnsureSuccessStatusCode();
                        var Result = await httpResponse.Content.ReadFromJsonAsync<TResult>();
                        httpResult = Result!;
                    }
                    catch (Exception ex)
                    {
                        throw new HttpRequestException($"Error requesting Qdrant data: {ex.Message}");
                    }
                               
                }
                break;

            case nameof(HttpMethod.Put):
                {
                    using HttpResponseMessage httpResponse = 
                        await httpClient.PutAsJsonAsync<TResult>(qdranturl, httpContentData!);
                    
                    try
                    {
                        httpResponse.EnsureSuccessStatusCode();
                        var Result = await httpResponse.Content.ReadFromJsonAsync<TResult>();
                        httpResult = Result!;
                    }
                    catch (Exception ex)
                    {
                        throw new HttpRequestException($"Error requesting Qdrant data: {ex.Message}");
                    }                    
                }
            
                break;

            case nameof(HttpMethod.Patch):
                {
                    using HttpResponseMessage httpResponse = 
                        await httpClient.PatchAsJsonAsync<TResult>(qdranturl, httpContentData!);

                    try
                    {
                        httpResponse.EnsureSuccessStatusCode();
                        var Result = await httpResponse.Content.ReadFromJsonAsync<TResult>();
                        httpResult = Result!;
                    }
                    catch (Exception ex)
                    {
                        throw new HttpRequestException($"Error requesting Qdrant data: {ex.Message}");
                    }
                
                }

                break;

            case nameof(HttpMethod.Delete):
                {
                    try
                    {
                        var Result = await httpClient.DeleteFromJsonAsync<TResult>(qdranturl);
                        httpResult = Result!;
                    }
                    catch (Exception ex)
                    {
                        throw new HttpRequestException($"Error requesting Qdrant data: {ex.Message}");
                    }
                }

                break;

            default:
                break;
        }

        return httpResult!;
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
