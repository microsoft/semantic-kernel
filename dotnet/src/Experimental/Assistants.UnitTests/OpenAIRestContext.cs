// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Xunit.Sdk;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// Placeholder context.
/// </summary>
internal sealed class OpenAIRestContext : IOpenAIRestContext
{
    /// <summary>
    /// Create a context from test configuration.
    /// </summary>
    /// <param name="httpClient">The http-client to utilize</param>
    /// <returns>A new context instance.</returns>
    public static OpenAIRestContext CreateFromConfig(HttpClient httpClient)
    {
        var apiKey =
            TestConfig.Configuration.GetValue<string>("OpenAIApiKey") ??
            throw new TestClassException("Missing OpenAI APIKey.");

        var context = new OpenAIRestContext(apiKey, httpClient);

        return context;
    }

    /// <inheritdoc/>
    public string ApiKey { get; }

    /// <inheritdoc/>
    public HttpClient HttpClient { get; }

    private OpenAIRestContext(string apiKey, HttpClient httpClient)
    {
        this.ApiKey = apiKey;
        this.HttpClient = httpClient;
    }
}
