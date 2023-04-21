// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for Azure speech recognition.
/// </summary>
public sealed class AzureSpeechOptions
{
    public const string PropertyName = "AzureSpeech";

    /// <summary>
    /// Region of the Azure speech service.
    /// </summary>
    public string Region { get; set; } = string.Empty;

    /// <summary>
    /// Key to access the Azure speech service.
    /// </summary>
    public string Key { get; set; } = string.Empty;
}
