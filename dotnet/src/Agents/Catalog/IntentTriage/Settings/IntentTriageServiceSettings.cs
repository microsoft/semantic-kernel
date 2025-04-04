// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// The settings associated with accessing the AI services required by the agent.
/// </summary>
internal sealed class IntentTriageServiceSettings
{
    /// <summary>
    /// The configuration keys.
    /// </summary>
    private static class Keys
    {
        public const string DeploymentName = "AzureOpenAI:DeploymentName";
        public const string Endpoint = "AzureOpenAI:Endpoint";
        public const string ApiKey = "AzureOpenAI:ApiKey";
        public const string ConnectionString = "AzureAI:ConnectionString";
    }

    /// <summary>
    /// The API key to connect to a chat-completion service (LLM).
    /// </summary>
    public string? ApiKey { get; init; }

    /// <summary>
    /// The connection string for connecting to a Foundry project.
    /// </summary>
    public string ConnectionString { get; init; } = string.Empty;

    /// <summary>
    /// The name of the chat-completion model deployment.
    /// </summary>
    /// <example>
    /// gpt-4o-mini
    /// </example>
    public string DeploymentName { get; init; } = string.Empty;

    /// <summary>
    /// The endpoint for the Azure AI service.
    /// </summary>
    public string Endpoint { get; init; } = string.Empty;

    /// <summary>
    /// Factory method to create <see cref="IntentTriageServiceSettings"/>
    /// from the active configuration.
    /// </summary>
    /// <param name="configuration">The active configuration</param>
    /// <remarks>
    /// Taking an explicit approach instead of a configuration binding
    /// we may not entirely control the definition of the configuration keys.
    /// Ultimately, the configuration can be accessed in any manner desired.
    /// </remarks>
    public static IntentTriageServiceSettings FromConfiguration(IConfiguration configuration)
    {
        return
            new IntentTriageServiceSettings
            {
                ApiKey = configuration[Keys.ApiKey],
                ConnectionString = configuration.GetRequiredValue(Keys.ConnectionString),
                DeploymentName = configuration.GetRequiredValue(Keys.DeploymentName),
                Endpoint = configuration.GetRequiredValue(Keys.Endpoint),
            };
    }
}
