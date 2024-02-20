// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// Execution settings for AssemblyAI speech-to-text execution.
/// </summary>
[Experimental("SKEXP0033")]
public class AssemblyAIAudioToTextExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// The time between each poll for the transcript status, until the status is completed.
    /// </summary>
    public TimeSpan PollingInterval { get; set; } = TimeSpan.FromSeconds(1);
}
