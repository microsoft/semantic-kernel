// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AudioToText;

/// <summary>
/// Interface for audio-to-text services.
/// </summary>
[Experimental("SKEXP0005")]
public interface IAudioToTextService : IAIService
{
    /// <summary>
    /// Get text content from audio stream.
    /// </summary>
    /// <param name="audio">Audio stream.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text content from audio stream.</returns>
    Task<TextContent> GetTextContentAsync(
        Stream audio,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}
