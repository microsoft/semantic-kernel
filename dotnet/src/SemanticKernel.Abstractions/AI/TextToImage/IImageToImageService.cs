// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.TextToImage;

/// <summary>
/// Provides image editing capabilities for AI services.
/// </summary>
[Experimental("SKEXP0010")]
public interface IImageToImageService
{
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
    Task<IReadOnlyList<ImageContent>> EditImageAsync(
        Stream image,
        string prompt,
        Stream? mask = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}
