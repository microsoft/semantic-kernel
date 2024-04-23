// Copyright (c) Microsoft. All rights reserved.
using System;
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
    /// Defineds polling behavior for Assistant API requests.
    /// </summary>
    public PollingConfiguration Polling { get; } = new PollingConfiguration();

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantConfiguration"/> class.
    /// </summary>
    /// <param name="apiKey">The Assistants API Key</param>
    /// <param name="endpoint">An optional endpoint if targeting Azure OpenAI Assistants API</param>
    public OpenAIAssistantConfiguration(string apiKey, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        if (!string.IsNullOrWhiteSpace(endpoint))
        {
            // Only verify `endpoint` when provided (AzureOAI vs OpenAI)
            Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        }

        this.ApiKey = apiKey;
        this.Endpoint = endpoint;
    }

    /// <summary>
    /// Configuration and defaults associated with polling behavior for Assistant API requests.
    /// </summary>
    public sealed class PollingConfiguration
    {
        /// <summary>
        /// The default polling interval when monitoring thread-run status.
        /// </summary>
        public static TimeSpan DefaultPollingInterval { get; } = TimeSpan.FromMilliseconds(500);

        /// <summary>
        /// The default back-off interval when  monitoring thread-run status.
        /// </summary>
        public static TimeSpan DefaultPollingBackoff { get; } = TimeSpan.FromSeconds(1);

        /// <summary>
        /// The default polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
        /// </summary>
        public static TimeSpan DefaultMessageSynchronizationDelay { get; } = TimeSpan.FromMilliseconds(500);

        /// <summary>
        /// The polling interval when monitoring thread-run status.
        /// </summary>
        public TimeSpan RunPollingInterval { get; set; } = DefaultPollingInterval;

        /// <summary>
        /// The back-off interval when  monitoring thread-run status.
        /// </summary>
        public TimeSpan RunPollingBackoff { get; set; } = DefaultPollingBackoff;

        /// <summary>
        /// The polling delay when retrying message retrieval due to a 404/NotFound from synchronization lag.
        /// </summary>
        public TimeSpan MessageSynchronizationDelay { get; set; } = DefaultMessageSynchronizationDelay;
    }
}
