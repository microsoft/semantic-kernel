// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.Configuration;
using Microsoft.Extensions.Configuration;

namespace ChatWithAgent.ApiService.Config;

/// <summary>
/// Service configuration.
/// </summary>
public sealed class ServiceConfig
{
    private readonly HostConfig _hostConfig;

    /// <summary>
    /// Initializes a new instance of the <see cref="ServiceConfig"/> class.
    /// </summary>
    /// <param name="configurationManager">The configuration manager.</param>
    public ServiceConfig(ConfigurationManager configurationManager)
    {
        this._hostConfig = new HostConfig(configurationManager);
    }

    /// <summary>
    /// Host configuration.
    /// </summary>
    public HostConfig Host => this._hostConfig;
}
