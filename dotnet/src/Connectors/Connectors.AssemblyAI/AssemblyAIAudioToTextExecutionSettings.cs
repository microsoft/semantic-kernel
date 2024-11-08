// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using AssemblyAI.Transcripts;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// Execution settings for AssemblyAI speech-to-text execution.
/// </summary>
public sealed class AssemblyAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// The time between each poll for the transcript status, until the status is completed.
    /// </summary>
    [JsonPropertyName("transcript_params")]
    public TranscriptOptionalParams? TranscriptParams
    {
        get => this._transcriptParams;
        set
        {
            this.ThrowIfFrozen();
            this._transcriptParams = value;
        }
    }

    /// <summary>
    /// The time between each poll for the transcript status, until the status is completed. Defaults to 3s.
    /// </summary>
    [JsonPropertyName("polling_interval")]
    public TimeSpan? PollingInterval
    {
        get => this._pollingInterval;
        set
        {
            this.ThrowIfFrozen();
            this._pollingInterval = value;
        }
    }

    /// <summary>
    /// How long to wait until the timeout exception thrown. Defaults to infinite.
    /// </summary>
    [JsonPropertyName("polling_timeout")]
    public TimeSpan? PollingTimeout
    {
        get => this._pollingTimeout;
        set
        {
            this.ThrowIfFrozen();
            this._pollingTimeout = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AssemblyAIAudioToTextExecutionSettings
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            PollingInterval = this.PollingInterval,
            PollingTimeout = this.PollingTimeout,
            ServiceId = this.ServiceId,
            TranscriptParams = this.TranscriptParams?.Clone()
        };
    }

    #region private ================================================================================

    private TimeSpan? _pollingInterval;
    private TimeSpan? _pollingTimeout;
    private TranscriptOptionalParams? _transcriptParams;

    #endregion
}
