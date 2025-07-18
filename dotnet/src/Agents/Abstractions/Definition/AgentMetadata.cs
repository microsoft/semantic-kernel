// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines agent metadata.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AgentMetadata
{
    /// <summary>
    /// Gets or sets the collection of authors associated with the agent.
    /// </summary>
    public IList<string>? Authors { get; set; }

    /// <summary>
    /// Gets or sets the collection of tags associated with the agent.
    /// </summary>
    public IList<string>? Tags { get; set; }

    /// <summary>
    /// Extra properties that may be included in the serialized agent metadata.
    /// </summary>
    /// <remarks>
    /// Used to store agent specific metadata.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object?> ExtensionData
    {
        get => this._extensionData ??= new Dictionary<string, object?>();
        set
        {
            Verify.NotNull(value);
            this._extensionData = value;
        }
    }

    #region private
    private IDictionary<string, object?>? _extensionData;
    #endregion
}
