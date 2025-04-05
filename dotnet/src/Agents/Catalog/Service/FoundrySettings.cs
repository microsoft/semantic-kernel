// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// The settings associated with accessing the AI services required by the agent.
/// </summary>
public sealed class FoundrySettings
{
    /// <summary>
    /// The configuration keys.
    /// </summary>
    private static class Keys
    {
        public const string DeploymentName = "foundry:deploymentname";
        public const string ConnectionString = "foundry:connectionstring";
    }

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
    /// Factory method to create <see cref="FoundrySettings"/>
    /// from the active configuration.
    /// </summary>
    /// <param name="configuration">The active configuration</param>
    /// <remarks>
    /// Taking an explicit approach instead of a configuration binding
    /// we may not entirely control the definition of the configuration keys.
    /// Ultimately, the configuration can be accessed in any manner desired.
    /// </remarks>
    public static FoundrySettings FromConfiguration(IConfiguration configuration)
    {
        return
            new FoundrySettings
            {
                ConnectionString = configuration.GetRequiredValue(Keys.ConnectionString),
                DeploymentName = configuration.GetRequiredValue(Keys.DeploymentName),
            };
    }
}
