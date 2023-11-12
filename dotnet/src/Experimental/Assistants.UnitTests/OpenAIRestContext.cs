// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Configuration;
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
    /// <param name="httpClient"></param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static OpenAIRestContext CreateFromConfig(HttpClient httpClient)
    {
        var apiKey =
            TestConfig.Configuration.GetValue<string>("OpenAIApiKey") ??
            throw new InvalidOperationException("$$$");

        var context = new OpenAIRestContext(apiKey, httpClient);
        return context;
    }

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
