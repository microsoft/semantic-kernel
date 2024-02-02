// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides execution settings for an AI request.
/// </summary>
/// <remarks>
/// Implementors of <see cref="ITextGenerationService"/> or <see cref="IChatCompletionService"/> can extend this
/// if the service they are calling supports additional properties. For an example, please reference
/// the Microsoft.SemanticKernel.Connectors.OpenAI.OpenAIPromptExecutionSettings implementation.
/// </remarks>
public class PromptExecutionSettings
{
    /// <summary>
    /// Gets the default service identifier.
    /// </summary>
    /// <remarks>
    /// In a dictionary of <see cref="PromptExecutionSettings"/>, this is the key that should be used settings considered the default.
    /// </remarks>
    public static string DefaultServiceId => "default";

    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    [JsonPropertyName("model_id")]
    public string? ModelId
    {
        get => this._modelId;

        set
        {
            if (this._isFrozen)
            {
                throw new InvalidOperationException("PromptExecutionSettings are frozen and ModelId cannot be modified.");
            }
            this._modelId = value;
        }
    }

    /// <summary>
    /// Extra properties that may be included in the serialized execution settings.
    /// </summary>
    /// <remarks>
    /// Avoid using this property if possible. Instead, use one of the classes that extends <see cref="PromptExecutionSettings"/>.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object>? ExtensionData
    {
        get => this._extensionData;

        set
        {
            if (this._isFrozen)
            {
                throw new InvalidOperationException("PromptExecutionSettings are frozen and ExtensionData cannot be modified.");
            }
            this._extensionData = value;
        }
    }

    /// <summary>
    /// Gets a value that indicates whether the <see cref="PromptExecutionSettings"/> are currently modifiable.
    /// </summary>
    public bool IsFrozen
    {
        get => this._isFrozen;
    }

    /// <summary>
    /// Makes the current <see cref="PromptExecutionSettings"/> unmodifiable and sets its IsFrozen property to true.
    /// </summary>
    public PromptExecutionSettings Freeze()
    {
        this._isFrozen = true;

        return this;
    }

    #region private ================================================================================

    private string? _modelId;
    private IDictionary<string, object>? _extensionData;
    private bool _isFrozen;

    #endregion
}
