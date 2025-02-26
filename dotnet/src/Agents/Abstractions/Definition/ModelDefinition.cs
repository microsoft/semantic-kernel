// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the model to be used by an agent.
/// </summary>
[ExcludeFromCodeCoverage]
public sealed class ModelDefinition
{
    /// <summary>
    /// The default API type.
    /// </summary>
    private const string DefaultApi = "chat";

    /// <summary>
    /// Gets or sets the ID of the model.
    /// </summary>
    public string? Id
    {
        get => this._id;
        set
        {
            Verify.NotNull(value);
            this._id = value;
        }
    }

    /// <summary>
    /// Gets or sets the type of API supported by the model.
    /// </summary>
    public string Api
    {
        get => this._api ?? DefaultApi;
        set
        {
            Verify.NotNull(value);
            this._api = value;
        }
    }

    /// <summary>
    /// Gets or sets the options used by the model.
    /// </summary>
    public PromptExecutionSettings? Options
    {
        get => this._options;
        set
        {
            Verify.NotNull(value);
            this._options = value;
        }
    }

    /// <summary>
    /// Gets or sets the options used by the model.
    /// </summary>
    public ModelConfiguration? Configuration
    {
        get => this._configuration;
        set
        {
            Verify.NotNull(value);
            this._configuration = value;
        }
    }

    #region
    private string? _id;
    private string? _api;
    private PromptExecutionSettings? _options;
    private ModelConfiguration? _configuration;
    #endregion
}
