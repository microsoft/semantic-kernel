// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// The settings associated with accessing the language services required by the agent.
/// </summary>
public sealed class IntentTriageLanguageSettings
{
    private const decimal DefaultAnalyzeThreshold = 0.60M;
    private const decimal DefaultQueryThreshold = 0.70M;

    /// <summary>
    /// The configuration keys.
    /// </summary>
    private static class Keys
    {
        public const string AnalyzeProject = "clu.projectName";
        public const string AnalyzeDeployment = "clu.deploymentName";
        public const string QueryProject = "cqa.projectName";
        public const string QueryDeployment = "cqa.deploymentName";
        public const string ApiEndpoint = "language.resourceUrl";
        public const string ApiKey = "language.resourceKey";
        public const string ApiVersion = "language.resourceVersion";
    }

    /// <summary>
    /// The project associated with the "analyze-conversations" API.
    /// </summary>
    public string AnalyzeProject { get; init; } = string.Empty;

    /// <summary>
    /// The deployment associated with the "analyze-conversations" API.
    /// </summary>
    public string AnalyzeDeployment { get; init; } = string.Empty;

    /// <summary>
    /// Confidence threshold for intent analysis.
    /// </summary>
    public decimal AnalyzeThreshold { get; init; } = DefaultAnalyzeThreshold;

    /// <summary>
    /// The project associated with the "query-knowledgebases" API.
    /// </summary>
    public string QueryProject { get; init; } = string.Empty;

    /// <summary>
    /// The deployment associated with the "query-knowledgebases" API.
    /// </summary>
    public string QueryDeployment { get; init; } = string.Empty;

    /// <summary>
    /// Confidence threshold for knowledgebase query.
    /// </summary>
    public decimal QueryThreshold { get; init; } = DefaultQueryThreshold;

    /// <summary>
    /// The language services endpoint (host only)
    /// </summary>
    public string ApiEndpoint { get; init; } = string.Empty;

    /// <summary>
    /// The API key for accessing the language services.
    /// </summary>
    public string ApiKey { get; init; } = string.Empty;

    /// <summary>
    /// The API version of the language services.
    /// </summary>
    public string ApiVersion { get; init; } = string.Empty;

    /// <summary>
    /// Factory method to create <see cref="IntentTriageLanguageSettings"/>
    /// from the active configuration.
    /// </summary>
    /// <param name="configuration">The active configuration</param>
    /// <remarks>
    /// Taking an explicit approach instead of a configuration binding
    /// we may not entirely control the definition of the configuration keys.
    /// Ultimately, the configuration can be accessed in any manner desired.
    /// </remarks>
    public static IntentTriageLanguageSettings FromConfiguration(IConfiguration configuration)
    {
        return
            new IntentTriageLanguageSettings
            {
                ApiEndpoint = configuration.GetRequiredValue(Keys.ApiEndpoint),
                ApiKey = configuration.GetRequiredValue(Keys.ApiKey),
                ApiVersion = configuration.GetRequiredValue(Keys.ApiVersion),
                AnalyzeProject = configuration.GetRequiredValue(Keys.AnalyzeProject),
                AnalyzeDeployment = configuration.GetRequiredValue(Keys.AnalyzeDeployment),
                AnalyzeThreshold = configuration.GetDecimalValue(Keys.AnalyzeProject, DefaultAnalyzeThreshold),
                QueryProject = configuration.GetRequiredValue(Keys.QueryProject),
                QueryDeployment = configuration.GetRequiredValue(Keys.QueryDeployment),
                QueryThreshold = configuration.GetDecimalValue(Keys.QueryProject, DefaultQueryThreshold),
            };
    }
}
