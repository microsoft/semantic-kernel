// Copyright (c) Microsoft. All rights reserved.

using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Ocr Support Configuration Options
/// </summary>
public class OcrSupportOptions
{
    public const string PropertyName = "OcrSupport";

    public enum OcrSupportType
    {
        /// <summary>
        /// No OCR Support
        /// </summary>
        None,

        /// <summary>
        /// Tesseract OCR Support
        /// </summary>
        Tesseract,

        /// <summary>
        /// Azure Form Recognizer OCR Support
        /// </summary>
        AzureFormRecognizer
    }

    /// <summary>
    /// Gets or sets the type of OCR support to use.
    /// </summary>
    public OcrSupportType Type { get; set; } = OcrSupportType.None;

    /// <summary>
    /// Gets or sets the configuration for Tesseract OCR support.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), OcrSupportType.Tesseract)]
    public TesseractOptions? Tesseract { get; set; }

    /// <summary>
    /// Gets or sets the configuration for Azure Form Recognizer OCR support.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), OcrSupportType.AzureFormRecognizer)]
    public AzureFormRecognizerOptions? AzureFormRecognizer { get; set; }
}
