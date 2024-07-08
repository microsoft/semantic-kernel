// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.Core;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Configuration to target a specific Open AI service.
/// </summary>
public sealed class OpenAIServiceConfiguration
{
    internal enum OpenAIServiceType
    {
        AzureOpenAI,
        OpenAI,
    }

    /// <summary>
    /// Produce a <see cref="OpenAIServiceConfiguration"/> that targets an Azure OpenAI endpoint using an API key.
    /// </summary>
    /// <param name="apiKey">The API key</param>
    /// <param name="endpoint">The service endpoint</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static OpenAIServiceConfiguration ForAzureOpenAI(string apiKey, Uri endpoint, HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey, nameof(apiKey));
        Verify.NotNull(endpoint, nameof(endpoint));

        return
            new()
            {
                ApiKey = apiKey,
                Endpoint = endpoint,
                HttpClient = httpClient,
                Type = OpenAIServiceType.AzureOpenAI,
            };
    }

    /// <summary>
    /// Produce a <see cref="OpenAIServiceConfiguration"/> that targets an Azure OpenAI endpoint using an token credentials.
    /// </summary>
    /// <param name="credential">The credentials</param>
    /// <param name="endpoint">The service endpoint</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static OpenAIServiceConfiguration ForAzureOpenAI(TokenCredential credential, Uri endpoint, HttpClient? httpClient = null)
    {
        Verify.NotNull(credential, nameof(credential));
        Verify.NotNull(endpoint, nameof(endpoint));

        return
            new()
            {
                Credential = credential,
                Endpoint = endpoint,
                HttpClient = httpClient,
                Type = OpenAIServiceType.AzureOpenAI,
            };
    }

    /// <summary>
    /// Produce a <see cref="OpenAIServiceConfiguration"/> that targets OpenAI services using an API key.
    /// </summary>
    /// <param name="apiKey">The API key</param>
    /// <param name="endpoint">An optional endpoint</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static OpenAIServiceConfiguration ForOpenAI(string? apiKey, Uri? endpoint = null, HttpClient? httpClient = null)
    {
        return
            new()
            {
                ApiKey = apiKey,
                Endpoint = endpoint,
                HttpClient = httpClient,
                Type = OpenAIServiceType.OpenAI,
            };
    }

    internal string? ApiKey { get; init; }
    internal TokenCredential? Credential { get; init; }
    internal Uri? Endpoint { get; init; }
    internal HttpClient? HttpClient { get; init; }
    internal OpenAIServiceType Type { get; init; }
}
