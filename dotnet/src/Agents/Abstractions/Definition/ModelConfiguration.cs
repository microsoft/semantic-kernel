// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Defines the configuration for a model.
/// </summary>
public sealed class ModelConfiguration
{
    /// <summary>
    /// The type of the model configuration.
    /// </summary>
    /// <remarks>
    /// Used to identify where the model is deployed e.g., "azure_openai" or "openai".
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
    /// Extra properties that may be included in the serialized model configuration.
    /// </summary>
    /// <remarks>
    /// Used to store model specific configuration e.g., the deployment name, endpoint, etc.
    /// </remarks>
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
    private string? _type;
    private IDictionary<string, object>? _extensionData;
    #endregion
}
