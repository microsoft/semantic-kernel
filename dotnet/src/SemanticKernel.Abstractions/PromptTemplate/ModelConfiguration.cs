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
    /// Used to identify where the model is deployed e.g., azure_openai, openai, ...
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

    /// <summary>
    /// Gets the value associated with the specified key.
    /// </summary>
    /// <param name="key">The key whose value to get.</param>
    /// <param name="value">When this method returns, the value associated with the specified key, if the key is found; otherwise, the default value for the type of the value parameter. This parameter is passed uninitialized.</param>
    public bool TryGetValue(string key, out object? value)
    {
        value = null;
        return this._extensionData?.TryGetValue(key, out value) ?? false;
    }

    #region private
    private string? _type;
    private IDictionary<string, object>? _extensionData;
    #endregion
}
