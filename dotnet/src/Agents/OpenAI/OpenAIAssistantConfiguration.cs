// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Configuration to target an OpenAI Assistant API.
/// </summary>
public sealed class OpenAIAssistantConfiguration
{
    /// <summary>
    /// The Assistants API Key.
    /// </summary>
    public string ApiKey { get; }

    /// <summary>
    /// An optional endpoint if targeting Azure OpenAI Assistants API.
    /// </summary>
    public string? Endpoint { get; }

    /// <summary>
    /// An optional API version override.
    /// </summary>
    public AssistantsClientOptions.ServiceVersion? Version { get; init; }

    /// <summary>
    /// Custom <see cref="HttpClient"/> for HTTP requests.
    /// </summary>
    public HttpClient? HttpClient { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantConfiguration"/> class.
    /// </summary>
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="endpoint">An optional endpoint if targeting Azure OpenAI Assistants API</param>
    public OpenAIAssistantConfiguration(string apiKey, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        if (string.IsNullOrWhiteSpace(endpoint))
        {
            Verify.StartsWith(endpoint!, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        }

        this.ApiKey = apiKey;
        this.Endpoint = endpoint;
    }
}
