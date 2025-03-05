// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.Configuration;
using Microsoft.Extensions.Configuration;

namespace ChatWithAgent.ApiService.Config;

/// <summary>
/// Service configuration.
/// </summary>
public sealed class ServiceConfig
{
    private readonly AgentConfig _agentConfig = new();
    private readonly HostConfig _hostConfig;

    /// <summary>
    /// Initializes a new instance of the <see cref="ServiceConfig"/> class.
    /// </summary>
    /// <param name="configurationManager">The configuration manager.</param>
    public ServiceConfig(ConfigurationManager configurationManager)
    {
        configurationManager
            .GetSection(AgentConfig.ConfigSectionName)
            .Bind(this._agentConfig);

        this._hostConfig = new HostConfig(configurationManager);
    }

    /// <summary>
    /// Agent configuration.
    /// </summary>
    public AgentConfig Agent => this._agentConfig;

    /// <summary>
    /// Host configuration.
    /// </summary>
    public HostConfig Host => this._hostConfig;
}
