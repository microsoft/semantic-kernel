// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for Tesseract OCR support.
/// </summary>
public sealed class TesseractOptions
{
    public const string PropertyName = "Tesseract";

    /// <summary>
    /// The file path where the Tesseract language file is stored (e.g. "./data")
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string? FilePath { get; set; } = string.Empty;

    /// <summary>
    /// The language file prefix name (e.g. "eng")
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string? Language { get; set; } = string.Empty;
}
