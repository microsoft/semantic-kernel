// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// $$$
/// </summary>
public sealed class OpenAIAssistantServiceOptions
{
    /// <summary>
    /// $$$
    /// </summary>
    public string ApiKey { get; }

    /// <summary>
    /// $$$ AZURE ONLY
    /// </summary>
    public string? Endpoint { get; }

    /// <summary>
    /// $$$
    /// </summary>
    public AssistantsClientOptions.ServiceVersion? Version { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    public HttpClient? HttpClient { get; init; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="apiKey"></param>
    /// <param name="endpoint"></param>
    public OpenAIAssistantServiceOptions(string apiKey, string? endpoint = null)
    {
        // $$$ VERIFY

        this.ApiKey = apiKey;
        this.Endpoint = endpoint;
    }
}
