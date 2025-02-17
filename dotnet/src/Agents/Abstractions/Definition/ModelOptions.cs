// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Definition;

/// <summary>
/// Defines the options used by a model.
/// </summary>
public sealed class ModelOptions
{
    /// <summary>
    /// The ID of the model.
    /// </summary>
    public string? ModelId
    {
        get => this._modelId;
        set
        {
            Verify.NotNull(value);
            this._modelId = value;
        }
    }

    /// <summary>
    /// Extra properties that may be included in the serialized model options.
    /// </summary>
    [JsonExtensionData]
    public IDictionary<string, object>? ExtensionData
    {
        get => this._extensionData;
        set
        {
            Verify.NotNull(value);
            this._extensionData = value;
        }
    }

    #region private
    private string? _modelId;
    private IDictionary<string, object>? _extensionData;
    #endregion
}
