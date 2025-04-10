// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the model to be used by an agent.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class ModelDefinition
{
    /// <summary>
    /// The default API type.
    /// </summary>
    private const string DefaultApi = "chat";

    /// <summary>
    /// Gets or sets the ID of the model.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or sets the type of API supported by the model.
    /// </summary>
    public string Api
    {
        get => this._api ?? DefaultApi;
        set
        {
            Verify.NotNullOrWhiteSpace(value);
            this._api = value;
        }
    }

    /// <summary>
    /// Gets or sets the options used by the model.
    /// </summary>
    public IDictionary<string, object>? Options { get; set; }

    /// <summary>
    /// Gets or sets the connection used by the model.
    /// </summary>
    public ModelConnection? Connection { get; set; }

    #region
    private string? _api;
    #endregion
}
