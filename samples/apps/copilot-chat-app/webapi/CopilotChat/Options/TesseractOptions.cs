// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for handling memorized documents.
/// </summary>
public class TesseractOptions
{
    public const string PropertyName = "Tesseract";

    /// <summary>
    /// Gets or sets the language of the Tesseract language data file located in the './tessdata' folder to use for OCR during document import.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Language { get; set; } = "eng";
}
