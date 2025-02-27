// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the model to be used by an agent.
/// </summary>
[ExcludeFromCodeCoverage]
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
            Verify.NotNull(value);
            this._api = value;
        }
    }

    /// <summary>
    /// Gets or sets the options used by the model.
    /// </summary>
    public PromptExecutionSettings? Options { get; set; }

    /// <summary>
    /// Gets or sets the options used by the model.
    /// </summary>
    public ModelConfiguration? Configuration { get; set; }

    #region
    private string? _api;
    #endregion
}
