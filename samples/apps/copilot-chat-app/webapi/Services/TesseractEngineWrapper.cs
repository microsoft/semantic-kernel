// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Tesseract;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Wrapper for the TesseractEngine within the Tesseract OCR library. This is used to allow the TesseractEngine to be mocked in the event that the Tesseract language file is not installed.
/// </summary>
public class TesseractEngineWrapper : IOcrEngine
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
    public async Task<string> ReadTextFromImageFileAsync(IFormFile imageFile)
    {
        await using (var ms = new MemoryStream())
        {
            await imageFile.CopyToAsync(ms);
            var fileBytes = ms.ToArray();
            await using var imgStream = new MemoryStream(fileBytes);

            using var img = Pix.LoadFromMemory(imgStream.ToArray());

            using var page = this.TesseractEngine.Process(img);
            return page.GetText();
        }
    }
}
