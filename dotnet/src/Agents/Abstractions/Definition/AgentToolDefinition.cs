// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// The options for defining a tool.
/// </summary>
public class AgentToolDefinition
{
    /// <summary>
    /// The type of the tool.
    /// </summary>
    /// <remarks>
    /// Used to identify which type of tool is being used e.g., code interpreter, openapi, ...
    /// </remarks>
    public string? Type
    {
        get => this._type;
        set
        {
            Verify.NotNull(value);
            this._type = value;
        }
    }

    /// <summary>
    /// The name of the tool.
    /// </summary>
    public string? Name
    {
        get => this._name;
        set
        {
            Verify.NotNull(value);
            this._name = value;
        }
    }

    /// <summary>
    /// The description of the tool.
    /// </summary>
    public string? Description
    {
        get => this._description;
        set
        {
            Verify.NotNull(value);
            this._description = value;
        }
    }

    /// <summary>
    /// Gets or sets the configuration for the tool.
    /// </summary>
    /// <remarks>
    /// Used to store tool specific configuration e.g., files associated with the tool, etc.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object>? Configuration
    {
        get => this._configuration;
        set
        {
            Verify.NotNull(value);
            this._configuration = value;
        }
    }

    /// <summary>
    /// Gets the required configuration.
    /// </summary>
    /// <param name="key">Name of the configuration value.</param>
    public object GetRequiredConfiguration(string key)
    {
        Verify.NotNull(key);
        Verify.True(this.Configuration!.ContainsKey(key), $"The configuration key '{key}' is required.");

        return this.Configuration[key];
    }

    #region private
    private string? _type;
    private string? _name;
    private string? _description;
    private IDictionary<string, object>? _configuration;
    #endregion
}
