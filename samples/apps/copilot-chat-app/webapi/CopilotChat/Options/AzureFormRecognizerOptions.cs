// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for Azure Form Recognizer OCR support.
/// </summary>
public sealed class AzureFormRecognizerOptions
{
    public const string PropertyName = "AzureFormRecognizer";

    /// <summary>
    /// The endpoint for accessing a provisioned Azure Form Recognizer instance
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string? Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// The provisioned Azure Form Recognizer access key
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string? Key { get; set; } = string.Empty;
}
