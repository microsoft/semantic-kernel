// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ChatWithAgent.Configuration;

/// <summary>
/// Azure OpenAI chat configuration.
/// </summary>
public sealed class AzureOpenAIChatConfig
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string ConfigSectionName = "AzureOpenAIChat";

    /// <summary>
    /// The name of the connection string of the Azure OpenAI chat service.
    /// </summary>
    public const string ConnectionStringName = ConfigSectionName;

    /// <summary>
    /// The name of the chat deployment.
    /// </summary>
    [Required]
    public string DeploymentName { get; set; } = string.Empty;

    /// <summary>
    /// The name of the chat model.
    /// </summary>
    public string ModelName { get; set; } = string.Empty;

    /// <summary>
    /// The chat model version.
    /// </summary>
    public string ModelVersion { get; set; } = string.Empty;
}
