// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// Execution settings for AssemblyAI speech-to-text execution.
/// </summary>
public sealed class AssemblyAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// The time between each poll for the transcript status, until the status is completed.
    /// </summary>
    [JsonPropertyName("polling_interval")]
    public TimeSpan PollingInterval
    {
        get => this._pollingInterval;
        set
        {
            this.ThrowIfFrozen();
            this._pollingInterval = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AssemblyAIAudioToTextExecutionSettings
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            PollingInterval = this.PollingInterval
        };
    }

    #region private ================================================================================

    private TimeSpan _pollingInterval = TimeSpan.FromSeconds(1);

    #endregion
}
