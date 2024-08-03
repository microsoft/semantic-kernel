// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.ImageToText;

/// <summary>
/// Interface for image-to-text services.
/// </summary>
[Experimental("SKEXP0001")]
public interface IImageToTextService : IAIService
{
    /// <summary>
    /// Get text content from image content.
    /// </summary>
    /// <param name="content">Image content.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text content from image content.</returns>
    Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        ImageContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}
