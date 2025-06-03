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
    /// Gets or sets the unique identifier of the model.
    /// </summary>
    /// <remarks>
    /// This is typically a short string, but can be any string that is compatible with the agent.
    /// Typically, depending on the provider, this can replace the entire connection settings if
    /// the provider has a way to resolve the model connection from the id.
    /// </remarks>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or sets the type of API used by the agent.
    /// </summary>
    /// <remarks>
    /// This is typically a chat or completion API, but can be any API that is compatible with the agent.
    /// </remarks>
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
    /// Gets or sets the options used by the agent.
    /// </summary>
    /// <remarks>
    /// This is typically a set of options that are compatible with the API and connection used by the agent.
    /// This optional section is used to specify the options to be used when executing the agent.
    /// If this section is not included, the runtime will use the default options for the API and connection used by the agent.
    /// </remarks>
    public IDictionary<string, object>? Options { get; set; }

    /// <summary>
    /// Gets or sets the connection used by the agent.
    /// </summary>
    /// <remarks>
    /// This is typically a type and deployment, but can be any connection that is compatible with the agent.
    /// The type parameter is used to tell the runtime how to load and execute the agent.
    /// The deployment parameter, in this example, is used to tell the runtime which deployment to use when executing against Azure OpenAI.
    /// </remarks>
    public ModelConnection? Connection { get; set; }

    #region
    private string? _api;
    #endregion
}
