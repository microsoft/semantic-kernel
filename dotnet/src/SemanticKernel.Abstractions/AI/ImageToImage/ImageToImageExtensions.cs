// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ImageToImage;

/// <summary>
/// Class that holds extension methods for the <see cref ="IImageToImageService" /> interface.
/// </summary>
public static class ImageToImageExtensions
{
    /// <summary>
    /// Modify an input PNG image using a given prompt.
    /// </summary>
    /// <param name="service">Image to image service</param>
    /// <param name="uri">URI of input PNG image</param>
    /// <param name="prompt">Prompt describing how to modify the output image</param>
    /// <param name="width">Output image width in pixels</param>
    /// <param name="height">Output image height in pixels</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image in PNG format</returns>
    public static async Task<byte[]> GenerateModifiedImageAsync(this IImageToImageService service, Uri uri, string prompt, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        using var httpClient = new HttpClient();

        byte[] inputFile = await httpClient.GetByteArrayAsync(uri).ConfigureAwait(false);

        return await service.GenerateModifiedImageAsync(inputFile, prompt, width, height, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Modify an input PNG image using a given prompt.
    /// </summary>
    /// <param name="service">Image to image service</param>
    /// <param name="inputFilePath">Location of input image</param>
    /// <param name="prompt">Prompt describing how to modify the output image</param>
    /// <param name="width">Output image width in pixels</param>
    /// <param name="height">Output image height in pixels</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image in PNG format</returns>
    public static async Task<byte[]> GenerateModifiedImageAsync(this IImageToImageService service, string inputFilePath, string prompt, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        byte[] inputFile = File.ReadAllBytes(inputFilePath);

        return await service.GenerateModifiedImageAsync(inputFile, prompt, width, height, kernel, cancellationToken).ConfigureAwait(false);
    }
}
