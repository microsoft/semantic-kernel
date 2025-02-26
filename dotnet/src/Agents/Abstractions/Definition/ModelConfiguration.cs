// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the configuration for a model.
/// </summary>
[ExcludeFromCodeCoverage]
public sealed class ModelConfiguration
{
    /// <summary>
    /// The type of the model configuration.
    /// </summary>
    /// <remarks>
    /// Used to identify the type of deployment e.g., azure_openai, openai, ...
    /// This type will also be used for configuration hosting.
    /// </remarks>
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the Service ID of the model configuration.
    /// </summary>
    public string? ServiceId { get; set; }

    /// <summary>
    /// Extra properties that may be included in the serialized model configuration.
    /// </summary>
    /// <remarks>
    /// Used to store model specific configuration e.g., the deployment name, endpoint, etc.
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
