// Copyright (c) Microsoft. All rights reserved.

/* 
Phase 02

- This class was created focused in the Image Generation using the SDK client instead of the own client in V1.
- Added Checking for empty or whitespace prompt.
- Removed the format parameter as this is never called in V1 code. Plan to implement it in the future once we change the ITextToImageService abstraction, using PromptExecutionSettings.
- Allow custom size for images when the endpoint is not the default OpenAI v1 endpoint.
*/

using System;
using System.ClientModel;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Images;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Generates an image with the provided configuration.
    /// </summary>
    /// <param name="prompt">Prompt to generate the image</param>
    /// <param name="width">Width of the image</param>
    /// <param name="height">Height of the image</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Url of the generated image</returns>
    internal async Task<string> GenerateImageAsync(
        string prompt,
        int width,
        int height,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var size = new GeneratedImageSize(width, height);

        EnsureSizeIsSupported(size, this.Endpoint!, this.ModelId);

        var imageOptions = new ImageGenerationOptions()
        {
            Size = size,
            ResponseFormat = GeneratedImageFormat.Uri
        };

        ClientResult<GeneratedImage> response = await RunRequestAsync(() => this.Client.GetImageClient(this.ModelId).GenerateImageAsync(prompt, imageOptions, cancellationToken)).ConfigureAwait(false);
        var generatedImage = response.Value;

        return generatedImage.ImageUri?.ToString() ?? throw new KernelException("The generated image is not in url format");
    }

    /// <summary>
    /// Ensures by throwing and exception if the requested image size is not supported by the OpenAI image generation models.
    /// </summary>
    /// <param name="targetSize">Target size to ensure support</param>
    /// <param name="endpoint">Current client endpoint</param>
    /// <param name="modelId">Target model identifier</param>
    /// <exception cref="ArgumentOutOfRangeException">Size is not supported</exception>
    private static void EnsureSizeIsSupported(GeneratedImageSize targetSize, Uri endpoint, string modelId)
    {
        // Only be restrictive to the image size if the endpoint is the default OpenAI v1 endpoint
        if (endpoint != new Uri(OpenAIV1Endpoint)) { return; }

        var supported = (targetSize == GeneratedImageSize.W256xH256 && modelId == "dall-e-2")
        || (targetSize == GeneratedImageSize.W512xH512 && modelId == "dall-e-2")
        || targetSize == GeneratedImageSize.W1024xH1024
        || (targetSize == GeneratedImageSize.W1024xH1792 && modelId == "dall-e-3")
        || (targetSize == GeneratedImageSize.W1792xH1024 && modelId == "dall-e-3");

        if (!supported)
        {
            throw new ArgumentOutOfRangeException($"The requested image size {targetSize} is not supported. Supported sizes are: 256x256 (dalle-2 only), 512x512 (dalle-2 only), 1024x1024, 1024x1792 (dalle-3 only), 1792x1024 (dalle-3 only)");
        }
    }
}
