// Copyright (c) Microsoft. All rights reserved.

using Tesseract;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Wrapper for the Tesseract engine.
/// </summary>
public interface ITesseractEngine
{
    //
    // Summary:
    //     Processes the specific image.
    //
    // Parameters:
    //   image:
    //     The image to process.
    //
    //   pageSegMode:
    //     The page layout analyasis method to use.
    //
    // Remarks:
    //     You can only have one result iterator open at any one time.
    Page Process(Pix image);
}
