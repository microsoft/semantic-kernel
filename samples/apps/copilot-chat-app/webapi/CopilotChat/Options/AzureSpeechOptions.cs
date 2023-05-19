// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for Azure speech recognition.
/// </summary>
public sealed class AzureSpeechOptions
{
    public const string PropertyName = "AzureSpeech";

    /// <summary>
    /// Location of the Azure speech service to use (e.g. "South Central US")
    /// </summary>
    public string? Region { get; set; } = string.Empty;

    /// <summary>
    /// Key to access the Azure speech service.
    /// </summary>
    public string? Key { get; set; } = string.Empty;
}
