// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Used as a placeholder implementation when "none" is set in the OcrSupport:Type field in the configuration.
/// </summary>
public class NullOcrEngine : IOcrEngine
{
    /// <summary>
    /// Throws an exception to let the user know they need to specify a valid OcrSupport type in order to use the image upload feature.
    /// </summary>
    /// <param name="imageFile">Not used</param>
    /// <returns>This will always throw a NotImplementedException</returns>
    /// <exception cref="NotImplementedException"></exception>
    public Task<string> ReadTextFromImageFileAsync(IFormFile imageFile)
    {
        throw new NotImplementedException("You must specify a \"Type\" other than \"none\" within the \"OcrSupport\" application settings to use the image upload feature. See the README.md");
    }
}
