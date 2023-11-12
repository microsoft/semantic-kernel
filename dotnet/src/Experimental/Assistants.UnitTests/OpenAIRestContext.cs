// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Experimental.Assistants;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// $$$
/// </summary>
internal class OpenAIRestContext : IOpenAIRestContext
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="apiKey"></param>
    /// <param name="httpClient"></param>
    public OpenAIRestContext(string apiKey, HttpClient httpClient)
    {
        this.ApiKey = apiKey;
        this.HttpClient = httpClient;
    }

    /// <inheritdoc/>
    public string ApiKey { get; }

    /// <inheritdoc/>
    public HttpClient HttpClient { get; }
}
