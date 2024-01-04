// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ImageToImage;

/// <summary>
/// Interface for image transformation (image to image)
/// </summary>
public interface IImageToImageService
{
    /// <summary>
    /// Modify an input PNG image using a given prompt.
    /// </summary>
    /// <param name="inputFile">Input PNG image's bytes</param>
    /// <param name="prompt">Prompt describing how to modify the output image</param>
    /// <param name="width">Output image width in pixels</param>
    /// <param name="height">Output image height in pixels</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image in PNG format</returns>
    public Task<byte[]> GenerateModifiedImageAsync(
        byte[] inputFile,
        string prompt,
        int width,
        int height,
        Kernel? kernel = null, // TODO: Is kernel even needed?
                               // TODO: Have the following??? PromptExecutionSettings? executionSettings = null
                               // TODO: Have Stable Diffusion img2ing settings object as input
        CancellationToken cancellationToken = default);
}
