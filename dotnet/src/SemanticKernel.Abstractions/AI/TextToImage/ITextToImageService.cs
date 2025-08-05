// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.TextToImage;

/// <summary>
/// Interface for text to image services
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextToImageService : IAIService
{
    /// <summary>
    /// Given a prompt and/or an input text, the model will generate a new image.
    /// </summary>
    /// <param name="input">Input text for image generation</param>
    /// <param name="executionSettings">Text to image execution settings</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Generated image contents</returns>
    [Experimental("SKEXP0001")]
    Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    );

    /// <summary>
    /// Generate edited images based on an original image and a text prompt.
    /// </summary>
    /// <param name="image">The image to edit</param>
    /// <param name="prompt">Text prompt describing the desired edits</param>
    /// <param name="mask">Optional mask indicating areas to edit</param>
    /// <param name="executionSettings">Execution settings</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Generated image contents</returns>
    [Experimental("SKEXP0001")]
    Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        Stream image,
        string prompt,
        Stream? mask = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    );

    /// <summary>
    /// Generate edited images based on file paths and a text prompt.
    /// </summary>
    /// <param name="imageFilePath">Path to the image file to edit</param>
    /// <param name="prompt">Text prompt describing the desired edits</param>
    /// <param name="maskFilePath">Optional path to mask file indicating areas to edit</param>
    /// <param name="executionSettings">Execution settings</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Generated image contents</returns>
    [Experimental("SKEXP0001")]
    Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        string imageFilePath,
        string prompt,
        string? maskFilePath = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    );
}
