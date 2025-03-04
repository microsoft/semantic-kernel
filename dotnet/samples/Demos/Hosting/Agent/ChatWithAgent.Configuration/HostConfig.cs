// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using Microsoft.Extensions.Configuration;

namespace ChatWithAgent.Configuration;

/// <summary>
/// Helper class for loading host configuration settings.
/// </summary>
public sealed class HostConfig
{
    /// <summary>
    /// The AI services section name.
    /// </summary>
    public const string AIServicesSectionName = "AIServices";

    private readonly AzureOpenAIChatConfig _azureOpenAIChat = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HostConfig"/> class.
    /// </summary>
    /// <param name="configurationManager">The configuration manager.</param>
    public HostConfig(ConfigurationManager configurationManager)
    {
        configurationManager
            .GetSection($"{AIServicesSectionName}:{AzureOpenAIChatConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIChat);
        configurationManager
            .Bind(this);
    }

    /// <summary>
    /// The AI chat service to use.
    /// </summary>
    [Required]
    public string AIChatService { get; set; } = string.Empty;

    /// <summary>
    /// The Azure OpenAI chat configuration.
    /// </summary>
    public AzureOpenAIChatConfig AzureOpenAIChat => this._azureOpenAIChat;
}
