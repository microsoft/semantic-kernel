// Copyright (c) Microsoft. All rights reserved.

using System;
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
    /// <inheritdoc/>
    public string ApiKey { get; }

    /// <inheritdoc/>
    public HttpClient GetHttpClient() => this._clientFactory.Invoke();

    private readonly Func<HttpClient> _clientFactory;

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

        var context = new OpenAIRestContext(apiKey, () => httpClient);

        return context;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIRestContext"/> class.
    /// </summary>
    private OpenAIRestContext(string apiKey, Func<HttpClient> clientFactory)
    {
        this._clientFactory = clientFactory;

        this.ApiKey = apiKey;
    }
}
