// Copyright (c) Microsoft. All rights reserved.

using System;
using Tesseract;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Used to mock the TesseractEngine in the event that the Tesseract language file is not installed.
/// </summary>
public class NullTesseractEngine : ITesseractEngine
{
    /// <summary>
    /// Throws an exception to let the user know they need to install the Tesseract language file.
    /// </summary>
    /// <param name="image">Not used</param>
    /// <returns>This will always throw a NotImplementedException</returns>
    /// <exception cref="NotImplementedException"></exception>
    public Page Process(Pix image)
    {
        throw new NotImplementedException("You must have the Tesseract language file to use the image upload feature. See the README.md");
    }
}
