// Copyright (c) Microsoft. All rights reserved.

namespace ProcessFramework.Aspire.Shared;

/// <summary>
/// Represents a request to translate a given text.
/// </summary>
public class TranslationRequest
{
    /// <summary>
    /// Gets or sets the text to be translated.
    /// </summary>
    public string TextToTranslate { get; set; } = string.Empty;
}
