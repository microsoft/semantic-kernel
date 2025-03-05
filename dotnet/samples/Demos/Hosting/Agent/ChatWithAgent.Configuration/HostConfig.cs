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

    private readonly ConfigurationManager _configurationManager;

    private readonly AzureOpenAIChatConfig _azureOpenAIChatConfig = new();

    private readonly OpenAIChatConfig _openAIChatConfig = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HostConfig"/> class.
    /// </summary>
    /// <param name="configurationManager">The configuration manager.</param>
    public HostConfig(ConfigurationManager configurationManager)
    {
        configurationManager
            .GetSection($"{AIServicesSectionName}:{AzureOpenAIChatConfig.ConfigSectionName}")
            .Bind(this._azureOpenAIChatConfig);
        configurationManager
            .GetSection($"{AIServicesSectionName}:{OpenAIChatConfig.ConfigSectionName}")
            .Bind(this._openAIChatConfig);
        configurationManager
            .Bind(this);

        this._configurationManager = configurationManager;
    }

    /// <summary>
    /// The AI chat service to use.
    /// </summary>
    [Required]
    public string AIChatService { get; set; } = string.Empty;

    /// <summary>
    /// The Azure OpenAI chat configuration.
    /// </summary>
    public AzureOpenAIChatConfig AzureOpenAIChat => this._azureOpenAIChatConfig;

    /// <summary>
    /// The OpenAI chat configuration.
    /// </summary>
    public OpenAIChatConfig OpenAIChat => this._openAIChatConfig;
}
