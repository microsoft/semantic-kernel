// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.TextToImage;

/// <summary>
/// Extension methods for <see cref="ITextToImageService"/>.
/// </summary>
public static class TextToImageServiceExtensions
{
    /// <summary>
    /// Given a prompt and/or an input text, the model will generate a new image.
    /// </summary>
    /// <param name="service">Target <see cref="ITextToImageService"/> instance</param>
    /// <param name="description">Image generation prompt</param>
    /// <param name="width">Image width in pixels</param>
    /// <param name="height">Image height in pixels</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image in base64 format or image URL</returns>
    public static async Task<string> GenerateImageAsync(this ITextToImageService service,
    string description,
    int width,
    int height,
    Kernel? kernel = null,
    CancellationToken cancellationToken = default)
    {
        var executionSettings = new PromptExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                { "width", width },
                { "height", height }
            }
        };

        var result = await service.GetImageContentsAsync(new TextContent(description), executionSettings, kernel, cancellationToken).ConfigureAwait(false);

        return result[0].Uri!.ToString();
    }
}
