// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Threading;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

public sealed partial class OpenAIAssistantAgent : Agent
{
    /// <summary>
    /// Specifies a key that avoids an exception from OpenAI Client when a custom endpoint is provided without an API key.
    /// </summary>
    private const string SingleSpaceKey = " ";

    /// <summary>
    /// Produces an <see cref="AzureOpenAIClient"/>.
    /// </summary>
    /// <param name="apiKey">The API key.</param>
    /// <param name="endpoint">The service endpoint.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static AzureOpenAIClient CreateAzureOpenAIClient(ApiKeyCredential apiKey, Uri endpoint, HttpClient? httpClient = null)
    {
        Verify.NotNull(apiKey, nameof(apiKey));
        Verify.NotNull(endpoint, nameof(endpoint));

        AzureOpenAIClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new AzureOpenAIClient(endpoint, apiKey!, clientOptions);
    }

    /// <summary>
    /// Produces an <see cref="AzureOpenAIClient"/>.
    /// </summary>
    /// <param name="credential">The credentials.</param>
    /// <param name="endpoint">The service endpoint.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static AzureOpenAIClient CreateAzureOpenAIClient(TokenCredential credential, Uri endpoint, HttpClient? httpClient = null)
    {
        Verify.NotNull(credential, nameof(credential));
        Verify.NotNull(endpoint, nameof(endpoint));

        AzureOpenAIClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new AzureOpenAIClient(endpoint, credential, clientOptions);
    }

    /// <summary>
    /// Produces an <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="endpoint">An optional endpoint.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static OpenAIClient CreateOpenAIClient(Uri? endpoint = null, HttpClient? httpClient = null)
    {
        OpenAIClientOptions clientOptions = CreateOpenAIClientOptions(endpoint, httpClient);
        return new OpenAIClient(new ApiKeyCredential(SingleSpaceKey), clientOptions);
    }

    /// <summary>
    /// Produces an <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="apiKey">The API key.</param>
    /// <param name="endpoint">An optional endpoint.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static OpenAIClient CreateOpenAIClient(ApiKeyCredential apiKey, Uri? endpoint = null, HttpClient? httpClient = null)
    {
        OpenAIClientOptions clientOptions = CreateOpenAIClientOptions(endpoint, httpClient);
        return new OpenAIClient(apiKey, clientOptions);
    }

    private static AzureOpenAIClientOptions CreateAzureClientOptions(HttpClient? httpClient)
    {
        AzureOpenAIClientOptions options = new();

        ConfigureClientOptions(httpClient, options);

        return options;
    }

    private static OpenAIClientOptions CreateOpenAIClientOptions(Uri? endpoint, HttpClient? httpClient)
    {
        OpenAIClientOptions options = new()
        {
            Endpoint = endpoint ?? httpClient?.BaseAddress,
        };

        ConfigureClientOptions(httpClient, options);

        return options;
    }

    private static void ConfigureClientOptions(HttpClient? httpClient, ClientPipelineOptions options)
    {
        options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIAssistantAgent))), PipelinePosition.PerCall);
        options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.UserAgent, $"{HttpHeaderConstant.Values.UserAgent} {nameof(OpenAIAssistantAgent)}"), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable default timeout
        }
    }

    private static GenericActionPipelinePolicy CreateRequestHeaderPolicy(string headerName, string headerValue)
        =>
            new((message) =>
            {
                var headers = message?.Request?.Headers;

                if (headers is not null)
                {
                    var value = !headers.TryGetValue(headerName, out string? existingHeaderValue) || string.IsNullOrWhiteSpace(existingHeaderValue) ?
                        headerValue :
                        $"{headerValue} {existingHeaderValue}";

                    headers.Set(headerName, value);
                }
            });
}
