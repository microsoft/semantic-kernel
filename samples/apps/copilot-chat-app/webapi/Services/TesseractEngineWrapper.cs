// Copyright (c) Microsoft. All rights reserved.

using System;
using Tesseract;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Wrapper for the TesseractEngine within the Tesseract OCR library. This is used to allow the TesseractEngine to be mocked in the event that the Tesseract language file is not installed.
/// </summary>
public class TesseractEngineWrapper : ITesseractEngine
{
    /// <summary>
    /// Creates a new instance of the TesseractEngineWrapper passing in a valid TesseractEngine.
    /// </summary>
    /// <param name="tesseractEngine"></param>
    public TesseractEngineWrapper(TesseractEngine tesseractEngine)
    {
        if (tesseractEngine == null)
        {
            throw new ArgumentNullException(nameof(tesseractEngine));
        }

        this.TesseractEngine = tesseractEngine;
    }

    /// <summary>
    /// Passes the TesseractEngine to the wrapper.
    /// </summary>
    public TesseractEngine TesseractEngine { get; }

    ///<inheritdoc/>
    public Page Process(Pix image)
    {
        return this.TesseractEngine.Process(image);
    }
}
